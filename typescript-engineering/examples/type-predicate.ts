export type AccountRecord = {
  accountId: string
  displayName: string
  isActive: boolean
}

export function isAccountRecord(value: unknown): value is AccountRecord {
  return (
    !!value &&
    typeof value === 'object' &&
    'accountId' in value &&
    'displayName' in value &&
    'isActive' in value
  )
}

export function readDisplayName(value: unknown) {
  if (!isAccountRecord(value)) {
    return 'Unknown account'
  }

  return value.displayName
}
