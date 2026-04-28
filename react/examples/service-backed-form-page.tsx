/**
 * House-style thin page shell example.
 *
 * This shows how page code composes shared form logic, foundation primitives,
 * and a service hook without pulling business rules into the component.
 */

import { Button } from './foundational-button'
import { Input } from './foundational-input'
import { useFormManagement } from './use-form-management'

type CommunityFormState = {
  community: {
    name: string
    slug: string
  }
}

type ValidationErrors = Partial<Record<'community.name' | 'community.slug', string>>

type UseCreateCommunityService = {
  createCommunity: (data: CommunityFormState) => Promise<void>
  errors: ValidationErrors
  isSubmitting: boolean
  submitError: string | null
}

declare function useCreateCommunityService(): UseCreateCommunityService

const initialState: CommunityFormState = {
  community: {
    name: '',
    slug: '',
  },
}

export function CreateCommunityPage() {
  const { createCommunity, errors, isSubmitting, submitError } = useCreateCommunityService()
  const form = useFormManagement({
    initialState,
    onSubmit: createCommunity,
  })

  return (
    <main>
      <h1>Create Community</h1>

      {submitError ? <p role="alert">{submitError}</p> : null}

      <form onSubmit={form.onSubmit}>
        <Input
          label="Community name"
          name="community.name"
          value={form.state.community.name}
          errorMessage={errors['community.name']}
          onChange={form.onChange}
        />

        <Input
          label="URL slug"
          name="community.slug"
          value={form.state.community.slug}
          errorMessage={errors['community.slug']}
          onChange={form.onChange}
        />

        <Button type="submit" isBusy={isSubmitting} disabled={!form.isDirty}>
          Create community
        </Button>
      </form>
    </main>
  )
}
