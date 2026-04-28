/**
 * Service-backed form page example for SolidJS.
 *
 * Demonstrates:
 * - Thin page shell composing foundational components and service hooks
 * - useAsyncSubscription for loading existing data
 * - useAsyncOperation (via a mutation hook) for the save action
 * - useFormManagement for controlled form state
 * - Async UI state branching with <Switch>/<Match> and <Show>
 * - Error surfacing through the Alert primitive
 * - Disabling submit during processing
 * - Redirect on success via createEffect
 */

import { type Component, Switch, Match, Show, createEffect } from 'solid-js'
import { useItemDetails, useUpsertItem } from '@/store/hooks/useItemDetails'
import { useActiveUser } from '@/store/service/auth'
import { Alert, Button, Input, LoadingSpinner } from '@/components/foundation'
import useFormManagement from '@/components/foundation/utils/useFormManagement'
import styles from './styles.module.css'

type ItemDetailsPageProps = {
  itemId: string
}

type FormData = {
  title: string
  description: string
}

const ItemDetailsPage: Component<ItemDetailsPageProps> = (props) => {
  const userState = useActiveUser()
  const itemData = useItemDetails(() => props.itemId)
  const upsertOp = useUpsertItem()

  const form = useFormManagement<FormData>(
    { title: '', description: '' },
    async (data) => {
      const userId = userState.data?.uid
      if (!userId) return
      const newId = await upsertOp.execute(userId, data, props.itemId)
      if (newId) window.location.href = `/items/${newId}`
    },
  )

  // Seed form when subscription data arrives
  createEffect(() => {
    if (itemData.status.isSuccess && itemData.data) {
      form.resetFormToNew({
        title: itemData.data.title,
        description: itemData.data.description,
      })
    }
  })

  // Redirect on save success — handled inside formSubmitCb above

  return (
    <div class={styles.page}>
      <Switch fallback={<p class={styles.fallback}>Something went wrong.</p>}>
        <Match when={itemData.status.isProcessing}>
          <LoadingSpinner />
        </Match>

        <Match when={itemData.status.isError}>
          <Alert errors={itemData.errors} />
        </Match>

        <Match when={itemData.status.isSuccess || props.itemId === 'NEW'}>
          <form class={styles.form} onSubmit={form.onSubmit}>
            <Alert errors={upsertOp.errors} />

            <Input
              name="title"
              label="Title"
              value={form.state.title}
              onInput={form.onChange}
              placeholder="Enter a title"
            />

            <Input
              name="description"
              label="Description"
              value={form.state.description}
              onInput={form.onChange}
              placeholder="Enter a description"
            />

            <div class={styles.actions}>
              <Button
                type="submit"
                disabled={upsertOp.status.isProcessing}
              >
                <Show when={upsertOp.status.isProcessing} fallback="Save">
                  Saving…
                </Show>
              </Button>
            </div>
          </form>
        </Match>
      </Switch>
    </div>
  )
}

export default ItemDetailsPage
