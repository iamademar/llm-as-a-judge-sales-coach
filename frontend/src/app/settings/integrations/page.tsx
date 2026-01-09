"use client"

import { useEffect, useState, useCallback } from "react"
import { Button } from "@/components/Button"
import { Card } from "@/components/Card"
import { Divider } from "@/components/Divider"
import { Input } from "@/components/Input"
import { Label } from "@/components/Label"
import { Badge } from "@/components/Badge"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/Dialog"
import { useAuth } from "@/app/auth/AuthContext"
import {
  fetchLLMCredentials,
  createLLMCredential,
  updateLLMCredential,
  deleteLLMCredential,
  type LLMCredential,
  type ProviderInfo,
  type LLMProvider,
} from "@/lib/api"
import {
  RiExternalLinkLine,
  RiCheckLine,
  RiCloseLine,
  RiKey2Line,
  RiEditLine,
  RiDeleteBinLine,
} from "@remixicon/react"

// Provider brand colors and icons
const providerStyles: Record<
  LLMProvider,
  { bgColor: string; textColor: string; icon: string }
> = {
  openai: {
    bgColor: "bg-emerald-50 dark:bg-emerald-950/30",
    textColor: "text-emerald-700 dark:text-emerald-400",
    icon: "🤖",
  },
  anthropic: {
    bgColor: "bg-orange-50 dark:bg-orange-950/30",
    textColor: "text-orange-700 dark:text-orange-400",
    icon: "🧠",
  },
  google: {
    bgColor: "bg-blue-50 dark:bg-blue-950/30",
    textColor: "text-blue-700 dark:text-blue-400",
    icon: "✨",
  },
}

interface ProviderCardProps {
  provider: ProviderInfo
  credential?: LLMCredential
  onAdd: (provider: LLMProvider, apiKey: string, defaultModel?: string) => Promise<void>
  onUpdate: (id: string, apiKey?: string, defaultModel?: string) => Promise<void>
  onDelete: (id: string) => Promise<void>
  isAdmin: boolean
}

function ProviderCard({
  provider,
  credential,
  onAdd,
  onUpdate,
  onDelete,
  isAdmin,
}: ProviderCardProps) {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [apiKey, setApiKey] = useState("")
  const [defaultModel, setDefaultModel] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const style = providerStyles[provider.id as LLMProvider]
  const isConfigured = !!credential

  const handleAdd = async () => {
    setIsLoading(true)
    setError(null)
    try {
      await onAdd(provider.id as LLMProvider, apiKey, defaultModel || undefined)
      setApiKey("")
      setDefaultModel("")
      setIsAddDialogOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add credential")
    } finally {
      setIsLoading(false)
    }
  }

  const handleUpdate = async () => {
    if (!credential) return
    setIsLoading(true)
    setError(null)
    try {
      await onUpdate(
        credential.id,
        apiKey || undefined,
        defaultModel || undefined
      )
      setApiKey("")
      setDefaultModel("")
      setIsEditDialogOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update credential")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!credential) return
    setIsLoading(true)
    setError(null)
    try {
      await onDelete(credential.id)
      setIsDeleteDialogOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete credential")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="px-4 pb-6 pt-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-lg ${style.bgColor}`}
            >
              <span className="text-xl">{style.icon}</span>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                {provider.name}
              </h4>
              <p className="text-xs text-gray-500">{provider.description}</p>
            </div>
          </div>
          <Badge variant={isConfigured ? "success" : "neutral"}>
            {isConfigured ? (
              <span className="flex items-center gap-1">
                <RiCheckLine className="size-3" />
                Configured
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <RiCloseLine className="size-3" />
                Not configured
              </span>
            )}
          </Badge>
        </div>

        {isConfigured && credential && (
          <div className="mt-4 rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
            <div className="flex items-center gap-2 text-sm">
              <RiKey2Line className="size-4 text-gray-400" />
              <span className="font-mono text-gray-600 dark:text-gray-400">
                {credential.masked_key}
              </span>
            </div>
            {credential.default_model && (
              <p className="mt-1 text-xs text-gray-500">
                Default model: {credential.default_model}
              </p>
            )}
            <p className="mt-1 text-xs text-gray-400">
              Last updated:{" "}
              {new Date(credential.updated_at).toLocaleDateString()}
            </p>
          </div>
        )}

        <div className="mt-4">
          <p className="text-xs text-gray-500">
            Default model:{" "}
            <span className="font-medium">{provider.default_model}</span>
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-gray-200 bg-gray-50 p-4 dark:border-gray-900 dark:bg-gray-900">
        <div className="flex items-center gap-2">
          {isConfigured && isAdmin && (
            <>
              <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="secondary" className="h-8 px-3 text-sm">
                    <RiEditLine className="mr-1 size-4" />
                    Edit
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Update {provider.name} API Key</DialogTitle>
                    <DialogDescription>
                      Enter a new API key to replace the existing one. Leave
                      blank to keep the current key.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div>
                      <Label htmlFor="edit-api-key" className="font-medium">
                        New API Key (optional)
                      </Label>
                      <Input
                        id="edit-api-key"
                        type="password"
                        placeholder={`Enter new ${provider.key_prefix}... key`}
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        className="mt-2"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-model" className="font-medium">
                        Default Model (optional)
                      </Label>
                      <Input
                        id="edit-model"
                        type="text"
                        placeholder={provider.default_model}
                        value={defaultModel}
                        onChange={(e) => setDefaultModel(e.target.value)}
                        className="mt-2"
                      />
                    </div>
                    {error && (
                      <p className="text-sm text-red-600 dark:text-red-400">
                        {error}
                      </p>
                    )}
                  </div>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="secondary">Cancel</Button>
                    </DialogClose>
                    <Button
                      onClick={handleUpdate}
                      disabled={isLoading || (!apiKey && !defaultModel)}
                    >
                      {isLoading ? "Saving..." : "Save Changes"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <Dialog
                open={isDeleteDialogOpen}
                onOpenChange={setIsDeleteDialogOpen}
              >
                <DialogTrigger asChild>
                  <Button
                    variant="secondary"
                    className="h-8 px-3 text-sm text-red-600 hover:text-red-700 dark:text-red-500"
                  >
                    <RiDeleteBinLine className="mr-1 size-4" />
                    Remove
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Remove {provider.name} Integration</DialogTitle>
                    <DialogDescription>
                      Are you sure you want to remove this API key? This action
                      cannot be undone and will disable {provider.name}{" "}
                      features.
                    </DialogDescription>
                  </DialogHeader>
                  {error && (
                    <p className="text-sm text-red-600 dark:text-red-400">
                      {error}
                    </p>
                  )}
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="secondary">Cancel</Button>
                    </DialogClose>
                    <Button
                      variant="destructive"
                      onClick={handleDelete}
                      disabled={isLoading}
                    >
                      {isLoading ? "Removing..." : "Remove"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </>
          )}

          {!isConfigured && isAdmin && (
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="primary" className="h-8 px-3 text-sm">
                  <RiKey2Line className="mr-1 size-4" />
                  Add API Key
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add {provider.name} API Key</DialogTitle>
                  <DialogDescription>
                    Enter your {provider.name} API key to enable AI-powered
                    features using their models.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label htmlFor="add-api-key" className="font-medium">
                      API Key <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="add-api-key"
                      type="password"
                      placeholder={`${provider.key_prefix}...`}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="mt-2"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Your API key will be encrypted and stored securely.
                    </p>
                  </div>
                  <div>
                    <Label htmlFor="add-model" className="font-medium">
                      Default Model (optional)
                    </Label>
                    <Input
                      id="add-model"
                      type="text"
                      placeholder={provider.default_model}
                      value={defaultModel}
                      onChange={(e) => setDefaultModel(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  {error && (
                    <p className="text-sm text-red-600 dark:text-red-400">
                      {error}
                    </p>
                  )}
                </div>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button variant="secondary">Cancel</Button>
                  </DialogClose>
                  <Button
                    onClick={handleAdd}
                    disabled={isLoading || !apiKey.trim()}
                  >
                    {isLoading ? "Adding..." : "Add API Key"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}

          {!isAdmin && !isConfigured && (
            <p className="text-sm text-gray-500">
              Contact an admin to configure this integration.
            </p>
          )}
        </div>

        <a
          href={provider.docs_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700 dark:text-indigo-500"
        >
          Get API Key
          <RiExternalLinkLine className="size-4 shrink-0" aria-hidden="true" />
        </a>
      </div>
    </Card>
  )
}

export default function Integrations() {
  const { accessToken, user } = useAuth()
  const [credentials, setCredentials] = useState<LLMCredential[]>([])
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isAdmin = user?.is_superuser ?? false

  const loadCredentials = useCallback(async () => {
    if (!accessToken) return

    try {
      setIsLoading(true)
      const data = await fetchLLMCredentials(accessToken)
      setCredentials(data.credentials)
      setProviders(data.providers)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load credentials")
    } finally {
      setIsLoading(false)
    }
  }, [accessToken])

  useEffect(() => {
    loadCredentials()
  }, [loadCredentials])

  const handleAdd = async (
    provider: LLMProvider,
    apiKey: string,
    defaultModel?: string
  ) => {
    if (!accessToken) return
    await createLLMCredential(
      { provider, api_key: apiKey, default_model: defaultModel },
      accessToken
    )
    await loadCredentials()
  }

  const handleUpdate = async (
    id: string,
    apiKey?: string,
    defaultModel?: string
  ) => {
    if (!accessToken) return
    const updateData: { api_key?: string; default_model?: string } = {}
    if (apiKey) updateData.api_key = apiKey
    if (defaultModel) updateData.default_model = defaultModel
    await updateLLMCredential(id, updateData, accessToken)
    await loadCredentials()
  }

  const handleDelete = async (id: string) => {
    if (!accessToken) return
    await deleteLLMCredential(id, accessToken)
    await loadCredentials()
  }

  const getCredentialForProvider = (providerId: string) => {
    return credentials.find((c) => c.provider === providerId)
  }

  const configuredCount = credentials.length
  const totalProviders = providers.length

  return (
    <>
      <div className="space-y-10">
        <section aria-labelledby="integrations-overview">
          <div className="grid grid-cols-1 gap-x-14 gap-y-8 md:grid-cols-3">
            <div>
              <h2
                id="integrations-overview"
                className="scroll-mt-10 font-semibold text-gray-900 dark:text-gray-50"
              >
                LLM Integrations
              </h2>
              <p className="mt-1 text-sm leading-6 text-gray-500">
                Connect your AI providers to enable transcript analysis and
                coaching features.
              </p>
              <div className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/30 dark:text-amber-400">
                <strong>Note:</strong> At least one provider must be configured
                to use AI features.
              </div>
            </div>
            <div className="md:col-span-2">
              <div className="mb-6 flex items-center justify-between rounded-lg bg-gray-50 p-4 dark:bg-gray-900">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
                    Integration Status
                  </p>
                  <p className="text-sm text-gray-500">
                    {configuredCount} of {totalProviders} providers configured
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {configuredCount > 0 ? (
                    <Badge variant="success">
                      <RiCheckLine className="mr-1 size-3" />
                      Ready
                    </Badge>
                  ) : (
                    <Badge variant="warning">
                      <RiCloseLine className="mr-1 size-3" />
                      Setup Required
                    </Badge>
                  )}
                </div>
              </div>

              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600" />
                </div>
              ) : error ? (
                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-400">
                  {error}
                </div>
              ) : (
                <div className="space-y-4">
                  {providers.map((provider) => (
                    <ProviderCard
                      key={provider.id}
                      provider={provider}
                      credential={getCredentialForProvider(provider.id)}
                      onAdd={handleAdd}
                      onUpdate={handleUpdate}
                      onDelete={handleDelete}
                      isAdmin={isAdmin}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
        <Divider />
        <section aria-labelledby="security-info">
          <div className="grid grid-cols-1 gap-x-14 gap-y-8 md:grid-cols-3">
            <div>
              <h2
                id="security-info"
                className="scroll-mt-10 font-semibold text-gray-900 dark:text-gray-50"
              >
                Security
              </h2>
              <p className="mt-1 text-sm leading-6 text-gray-500">
                How we protect your API keys.
              </p>
            </div>
            <div className="md:col-span-2">
              <Card className="p-4">
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Encrypted at rest:
                      </strong>{" "}
                      All API keys are encrypted using AES-128 before storage.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Never exposed:
                      </strong>{" "}
                      Keys are never returned in API responses, only masked
                      versions are shown.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Organization-scoped:
                      </strong>{" "}
                      Credentials are isolated to your organization.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Admin-only access:
                      </strong>{" "}
                      Only organization admins can add, modify, or delete
                      credentials.
                    </span>
                  </li>
                </ul>
              </Card>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}

