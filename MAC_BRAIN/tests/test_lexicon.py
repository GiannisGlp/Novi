import tempfile
import unittest
from pathlib import Path

from MAC_BRAIN.lexicon import LearnedPreferences, Lexicon, LexiconStatus, Scope
from MAC_BRAIN.storage import DurableMemoryStore


class LexiconTests(unittest.TestCase):
    def test_single_phrase_not_globally_adopted(self):
        lex = Lexicon()
        entry = lex.observe("rizz", source="speech")
        self.assertLess(entry.frequency, Lexicon.GLOBAL_ADOPTION_FREQ)
        self.assertNotIn("rizz", lex.vocabulary_for("anyone"))
        self.assertNotEqual(entry.status, LexiconStatus.ADOPTED)

    def test_repeated_global_phrase_becomes_adopted(self):
        lex = Lexicon()
        for _ in range(Lexicon.GLOBAL_ADOPTION_FREQ):
            lex.observe("rizz", source="speech", appropriateness=0.8)
        self.assertEqual(lex.status_of("rizz"), LexiconStatus.ADOPTED)
        self.assertIn("rizz", lex.vocabulary_for("alice"))

    def test_relationship_scoped_word_stays_scoped(self):
        lex = Lexicon()
        for _ in range(6):
            lex.observe("bubby", source="speech", person="alice", scope=Scope.RELATIONSHIP)
        self.assertEqual(lex.status_of("bubby", person="alice"), LexiconStatus.SCOPED)
        # usable with alice (private audience), NOT with a stranger present
        self.assertTrue(lex.is_usable("bubby", person="alice", stranger_present=False))
        self.assertFalse(lex.is_usable("bubby", person="alice", stranger_present=True))
        # not usable with bob at all
        self.assertFalse(lex.is_usable("bubby", person="bob"))
        self.assertNotIn("bubby", lex.vocabulary_for("bob"))

    def test_global_word_usable_in_any_audience(self):
        lex = Lexicon()
        for _ in range(Lexicon.GLOBAL_ADOPTION_FREQ):
            lex.observe("hello", source="core", appropriateness=1.0)
        self.assertTrue(lex.is_usable("hello", stranger_present=True))

    def test_deprecate_and_reject(self):
        lex = Lexicon()
        for _ in range(Lexicon.GLOBAL_ADOPTION_FREQ):
            lex.observe("old", source="speech", appropriateness=0.8)
        lex.deprecate("old")
        self.assertEqual(lex.status_of("old"), LexiconStatus.DEPRECATED)
        self.assertFalse(lex.is_usable("old"))

    def test_seed_core_vocabulary_is_adopted(self):
        lex = Lexicon(seed={"novi": "self name"})
        self.assertEqual(lex.status_of("novi"), LexiconStatus.ADOPTED)
        self.assertIn("novi", lex.vocabulary_for("anyone"))


class LearnedPreferencesTests(unittest.TestCase):
    def test_confidence_rises_with_evidence(self):
        prefs = LearnedPreferences()
        prefs.learn("alice", "response_length", "short")
        c1 = prefs.preference_for("alice", "response_length", default="medium")
        self.assertEqual(c1, "short")
        # more evidence strengthens confidence
        first = prefs._prefs[("alice", "response_length")].confidence
        prefs.learn("alice", "response_length", "short")
        second = prefs._prefs[("alice", "response_length")].confidence
        self.assertGreater(second, first)

    def test_correction_supersedes_older_preference(self):
        prefs = LearnedPreferences()
        prefs.learn("alice", "name", "Ali", explicit=True)
        prefs.record_correction("alice", "name", "Alison")
        self.assertEqual(prefs.preference_for("alice", "name", default=""), "Alison")
        # the correction supersedes the older value with strong confidence
        self.assertTrue(prefs._prefs[("alice", "name")].active)
        self.assertGreaterEqual(prefs._prefs[("alice", "name")].confidence, 0.9)

    def test_preference_falls_back_to_default_and_respects_context_override(self):
        prefs = LearnedPreferences()
        self.assertEqual(prefs.preference_for("bob", "humor", default="neutral"), "neutral")
        self.assertEqual(prefs.preference_for("bob", "detail", default="short", context_override="long"), "long")

    def test_preference_is_not_permission(self):
        prefs = LearnedPreferences()
        pref = prefs.learn("alice", "greeting", "yo")
        snap = pref.snapshot()
        self.assertNotIn("authorized", snap)
        self.assertNotIn("permission", snap)

    def test_person_scoped_preference_not_global(self):
        prefs = LearnedPreferences()
        prefs.learn("alice", "humor", "playful")
        self.assertEqual(prefs.preference_for("alice", "humor", default="neutral"), "playful")
        # bob has no such preference -> default
        self.assertEqual(prefs.preference_for("bob", "humor", default="neutral"), "neutral")


class DurableLexiconTests(unittest.TestCase):
    def test_lexicon_and_preferences_persist(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "learn.db"
            store = DurableMemoryStore(db)
            lex = Lexicon()
            for _ in range(3):
                lex.observe("rizz", source="speech", appropriateness=0.8)
            prefs = LearnedPreferences()
            prefs.record_correction("alice", "response_length", "short")
            store.save_lexicon(lex.snapshot())
            store.save_preferences(prefs.snapshot())
            store.close()

            reopened = DurableMemoryStore(db)
            lex2 = Lexicon.from_snapshot(reopened.load_lexicon())
            prefs2 = LearnedPreferences.from_snapshot(reopened.load_preferences())
            self.assertEqual(lex2.status_of("rizz"), LexiconStatus.ADOPTED)
            self.assertEqual(prefs2.preference_for("alice", "response_length"), "short")
            reopened.close()


if __name__ == "__main__":
    unittest.main()
