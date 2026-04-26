import type { User } from './shared-types'
import { createUser } from './user-factory'

export type UserSummary = {
  userId: User['userId']
  displayName: User['displayName']
}

export function buildUserSummary(userId: string): UserSummary {
  const user = createUser(userId)

  return {
    userId: user.userId,
    displayName: user.displayName,
  }
}
