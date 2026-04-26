import type { User } from './shared-types'

export function createUser(userId: string): User {
  return {
    userId,
    displayName: `user:${userId}`,
  }
}
