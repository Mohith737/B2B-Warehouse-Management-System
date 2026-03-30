// client/src/design-system/ui/molecules/SearchBar.tsx
import { Search } from '@carbon/react'
import { useEffect, useState } from 'react'

type SearchBarProps = {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  isLoading?: boolean
}

export function SearchBar({
  value,
  onChange,
  placeholder = 'Search',
  isLoading = false,
}: SearchBarProps): JSX.Element {
  const [localValue, setLocalValue] = useState(value)

  useEffect(() => {
    setLocalValue(value)
  }, [value])

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      onChange(localValue)
    }, 300)

    return () => {
      window.clearTimeout(timeoutId)
    }
  }, [localValue, onChange])

  return (
    <Search
      disabled={isLoading}
      id="search-bar"
      labelText="Search"
      onChange={(event) => setLocalValue(event.target.value)}
      placeholder={placeholder}
      size="lg"
      value={localValue}
    />
  )
}
