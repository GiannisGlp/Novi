export function ConnectionBanner({ show }: { show: boolean }) {
  return (
    <div id="connBanner" role="alert" className={show ? 'show' : undefined}>
      Lost connection to the Novi brain — waiting to reconnect…
    </div>
  )
}
