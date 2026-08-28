import { useState } from 'react'

export interface SearchRowProps {
  id?: string
  placeholder: string
  label: string
  buttonText: string
  onSearch: (query: string) => void
}

/** Input + button row (memory search, entity lookup). Enter triggers the search. */
export function SearchRow({ id, placeholder, label, buttonText, onSearch }: SearchRowProps) {
  const [q, setQ] = useState('')
  const run = () => onSearch(q)
  return (
    <div className="searchrow">
      <input
        id={id}
        placeholder={placeholder}
        aria-label={label}
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            run()
          }
        }}
      />
      <button onClick={run}>{buttonText}</button>
    </div>
  )
}
