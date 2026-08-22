"""Dedicated tests for `MAC_BRAIN/event_bus.py` (gap-analysis Step 3, item 17).

Covers the canonical doc-10 event-bus contract: typed envelope with
correlation/causation IDs, timestamps, priority, privacy class, replay,
deduplication, bounded-queue backpressure, health metrics, and access
control — plus the runtime wiring (MacBrain._emit publishes through the bus).
"""

import unittest

from MAC_BRAIN.event_bus import (
    DEFAULT_PRIORITY,
    DEFAULT_PRIVACY,
    EventBus,
    EventEnvelope,
)


class EventBusEnvelopeTests(unittest.TestCase):
    def test_publish_builds_canonical_envelope(self):
        bus = EventBus()
        e = bus.publish("perception.completed", {"detections": 2}, source="vision")
        self.assertIsInstance(e, EventEnvelope)
        self.assertTrue(e.event_id)
        self.assertEqual(e.event_type, "perception.completed")
        self.assertEqual(e.version, 1)
        self.assertTrue(e.occurred_at)
        self.assertTrue(e.published_at)
        self.assertEqual(e.source, "vision")
        self.assertTrue(e.correlation_id)
        self.assertTrue(e.causation_id)
        self.assertEqual(e.priority, DEFAULT_PRIORITY)
        self.assertEqual(e.privacy_class, DEFAULT_PRIVACY)
        self.assertEqual(e.payload, {"detections": 2})
        self.assertEqual(e.sequence, 1)

    def test_snapshot_has_legacy_and_canonical_keys(self):
        bus = EventBus()
        e = bus.publish("soul.updated", {"tone": "neutral"})
        snap = e.snapshot()
        # Legacy consumers read event_type; canonical contract reads type.
        self.assertEqual(snap["event_type"], "soul.updated")
        self.assertEqual(snap["type"], "soul.updated")
        self.assertIn("event_id", snap)
        self.assertIn("occurred_at", snap)
        self.assertIn("published_at", snap)
        self.assertIn("sequence", snap)

    def test_correlation_and_causation_threading(self):
        bus = EventBus()
        a = bus.publish("sense", {"v": 1}, correlation_id="corr-1")
        b = bus.publish("act", {"v": 2}, correlation_id="corr-1")
        # Same correlation domain; b is caused by a (the prior event).
        self.assertEqual(a.correlation_id, b.correlation_id)
        self.assertEqual(b.causation_id, a.event_id)

    def test_open_correlation_defaults_unique(self):
        bus = EventBus()
        a = bus.publish("evt", {})
        b = bus.publish("evt", {})
        self.assertNotEqual(a.correlation_id, b.correlation_id)

    def test_priority_and_privacy_normalized(self):
        bus = EventBus()
        e = bus.publish("safety", {}, priority="critical", privacy_class="private")
        self.assertEqual(e.priority, "critical")
        self.assertEqual(e.privacy_class, "private")
        # Unknown values fall back to defaults.
        e2 = bus.publish("x", {}, priority="bogus", privacy_class="bogus")
        self.assertEqual(e2.priority, DEFAULT_PRIORITY)
        self.assertEqual(e2.privacy_class, DEFAULT_PRIVACY)


class EventBusDedupTests(unittest.TestCase):
    def test_duplicate_publication_collapses(self):
        bus = EventBus()
        e1 = bus.publish("sensor.frame", {"frame_id": "f1"}, correlation_id="c", causation_id="root", source="cam")
        e2 = bus.publish("sensor.frame", {"frame_id": "f1"}, correlation_id="c", causation_id="root", source="cam")
        self.assertIs(e1, e2)
        self.assertEqual(bus.latest_sequence(), 1)
        health = bus.health()
        self.assertEqual(health["published"], 1)
        self.assertEqual(health["deduped"], 1)

    def test_different_payload_not_deduped(self):
        bus = EventBus()
        e1 = bus.publish("sensor.frame", {"frame_id": "f1"}, correlation_id="c", source="cam")
        e2 = bus.publish("sensor.frame", {"frame_id": "f2"}, correlation_id="c", source="cam")
        self.assertIsNot(e1, e2)
        self.assertEqual(bus.health()["published"], 2)


class EventBusReplayTests(unittest.TestCase):
    def test_replay_ordered_and_filterable(self):
        bus = EventBus()
        bus.publish("perception", {"n": 1})
        bus.publish("cognition", {"n": 2})
        bus.publish("action", {"n": 3})
        replay = bus.replay()
        self.assertEqual([e["event_type"] for e in replay], ["perception", "cognition", "action"])
        only_action = bus.replay(event_type="action")
        self.assertEqual(len(only_action), 1)
        self.assertEqual(only_action[0]["payload"], {"n": 3})

    def test_replay_by_correlation_id(self):
        bus = EventBus()
        bus.publish("a", {}, correlation_id="grp-1")
        bus.publish("b", {}, correlation_id="grp-1")
        bus.publish("c", {}, correlation_id="grp-2")
        group = bus.replay(correlation_id="grp-1")
        self.assertEqual(len(group), 2)

    def test_since_incremental(self):
        bus = EventBus()
        bus.publish("a", {})
        bus.publish("b", {})
        seq = bus.latest_sequence()
        bus.publish("c", {})
        since = bus.since(seq)
        self.assertEqual([e["event_type"] for e in since], ["c"])


class EventBusBackpressureTests(unittest.TestCase):
    def test_bounded_queue_drops_oldest(self):
        bus = EventBus(max_events=3)
        for i in range(5):
            bus.publish("burst", {"i": i})
        health = bus.health()
        self.assertEqual(health["retained"], 3)
        self.assertEqual(health["dropped"], 2)
        # The oldest events were evicted; the newest remain.
        kept = list(bus.events())
        self.assertEqual(len(kept), 3)
        newest = [e.payload["i"] for e in kept]
        self.assertEqual(newest, [2, 3, 4])

    def test_priority_aware_delivery(self):
        bus = EventBus()
        bus.publish("interactive", {}, priority="normal")
        bus.publish("high_value", {}, priority="high")
        bus.publish("safety", {}, priority="critical")
        high_plus = bus.events(priority_min="high")
        self.assertEqual([e.event_type for e in high_plus], ["high_value", "safety"])


class EventBusAccessControlTests(unittest.TestCase):
    def test_access_level_withholds_private_events(self):
        bus = EventBus()
        bus.publish("public_event", {}, privacy_class="public")
        bus.publish("unclassified_event", {}, privacy_class="unclassified")
        bus.publish("restricted_event", {}, privacy_class="restricted")
        bus.publish("private_event", {}, privacy_class="private")
        # unclassified consumer: only public + unclassified.
        default_view = bus.events(access_level="unclassified")
        self.assertEqual(
            {e.event_type for e in default_view},
            {"public_event", "unclassified_event"},
        )
        # restricted consumer additionally sees restricted.
        restricted_view = bus.events(access_level="restricted")
        self.assertEqual(
            {e.event_type for e in restricted_view},
            {"public_event", "unclassified_event", "restricted_event"},
        )
        # private consumer sees everything.
        private_view = bus.events(access_level="private")
        self.assertEqual(len(private_view), 4)

    def test_replay_respects_access(self):
        bus = EventBus()
        bus.publish("secret", {}, privacy_class="private")
        replay = bus.replay(access_level="unclassified")
        self.assertEqual(replay, ())
        private = bus.replay(access_level="private")
        self.assertEqual(len(private), 1)


class EventBusHealthTests(unittest.TestCase):
    def test_health_counts(self):
        bus = EventBus()
        bus.publish("a", {})
        bus.publish("a", {})
        bus.publish("b", {})
        health = bus.health()
        self.assertEqual(health["published"], 3)
        self.assertEqual(health["deduped"], 0)  # causation differs → not dupes
        self.assertEqual(health["per_type"], {"a": 2, "b": 1})
        self.assertEqual(health["retained"], 3)


class RuntimeEventBusWiringTests(unittest.TestCase):
    def test_runtime_emits_through_event_bus(self):
        from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
        from MAC_BRAIN.tests.test_mac_brain import FakeCamera

        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.step()
        brain.stop()
        # Events are on the bus with envelope fields, and the flattened view
        # is still the legacy dict list.
        self.assertGreater(brain.event_bus.latest_sequence(), 0)
        all_events = list(brain.event_bus.events())
        env = all_events[-1]
        self.assertTrue(env.event_id)
        self.assertTrue(env.correlation_id)
        # Each cycle is one correlation domain: start() (cycle 0) plus each
        # step() rotate the correlation id, so we see N+1 distinct domains and
        # each step's events share one correlation.
        groups: dict[str, list[str]] = {}
        for e in all_events:
            groups.setdefault(e.correlation_id, []).append(e.event_type)
        self.assertGreaterEqual(len(groups), 3)  # start domain + 2 step domains
        multi_event_domains = [ev for ev in groups.values() if len(ev) > 1]
        self.assertGreaterEqual(len(multi_event_domains), 2)  # both steps emit several events
        # The flattened legacy view still exposes the last event.
        self.assertEqual(brain.events[-1]["event_type"], env.event_type)

    def test_runtime_event_bus_health_available(self):
        from MAC_BRAIN.runtime import MacBrain, MacBrainConfig
        from MAC_BRAIN.tests.test_mac_brain import FakeCamera

        brain = MacBrain(camera=FakeCamera(), config=MacBrainConfig(curiosity_enabled=False))
        brain.start()
        brain.step()
        brain.stop()
        health = brain.event_bus.health()
        self.assertGreater(health["published"], 0)
        self.assertIn("per_type", health)


if __name__ == "__main__":
    unittest.main()
