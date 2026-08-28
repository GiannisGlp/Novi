import type { PreviewFace, PreviewFrame, PreviewTrack } from '../api/types'

export interface OverlayBox {
  left: number
  top: number
  width: number
  height: number
  cls: string
  label: string
}

type Det = NonNullable<PreviewFrame['detections']>[number]

/**
 * Pure port of the legacy camera overlay. Computes absolute-positioned boxes
 * over a letterboxed image inside a container of cw×ch CSS px, mirroring
 * drawOverlay's ordering: stable tracks first, then the SFace face box, then
 * raw detections that have no matching track yet.
 */
export function computeOverlayBoxes(
  dets: Det[] | undefined,
  faceInfo: PreviewFace | undefined,
  tracks: PreviewTrack[] | undefined,
  iw: number,
  ih: number,
  cw: number,
  ch: number,
): OverlayBox[] {
  const boxes: OverlayBox[] = []
  if (!iw || !ih || !cw || !ch) return boxes
  const scale = Math.min(cw / iw, ch / ih)
  const ox = (cw - iw * scale) / 2
  const oy = (ch - ih * scale) / 2
  const box = (x: number, y: number, w: number, h: number, cls: string, label: string) => {
    boxes.push({
      left: ox + x * scale,
      top: oy + y * scale,
      width: w * scale,
      height: h * scale,
      cls,
      label,
    })
  }

  // 1. tracked objects + people (stable ids, names when recognized)
  for (const t of tracks ?? []) {
    if (!Array.isArray(t.bbox)) continue
    if (t.is_person) {
      box(t.bbox[0], t.bbox[1], t.bbox[2], t.bbox[3], 'face', t.name || 'person')
    } else {
      box(t.bbox[0], t.bbox[1], t.bbox[2], t.bbox[3], 'obj', `${t.label} #${t.track_id}`)
    }
  }
  // 2. the SFace-identified face box (authoritative name/tier)
  if (faceInfo && Array.isArray(faceInfo.bbox)) {
    const nm = faceInfo.person
      ? `${faceInfo.person} (${faceInfo.tier})`
      : faceInfo.proposal
        ? 'new person — enroll below'
        : 'person?'
    box(faceInfo.bbox[0], faceInfo.bbox[1], faceInfo.bbox[2], faceInfo.bbox[3], 'face', nm)
  }
  // 3. raw detections with pixel bboxes but no track yet (unconfirmed)
  for (const d of dets ?? []) {
    if (
      Array.isArray(d.bbox) &&
      !(tracks ?? []).some(
        (t) =>
          Array.isArray(t.bbox) && t.bbox[0] === d.bbox![0] && t.bbox[1] === d.bbox![1],
      )
    ) {
      box(d.bbox[0], d.bbox[1], d.bbox[2], d.bbox[3], 'obj', `${d.label} ${Math.round((d.confidence || 0) * 100)}%`)
    }
  }
  return boxes
}
