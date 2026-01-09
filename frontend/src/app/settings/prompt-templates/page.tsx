"use client"

import { useEffect, useState, useCallback } from "react"
import { Button } from "@/components/Button"
import { Card } from "@/components/Card"
import { Divider } from "@/components/Divider"
import { Input } from "@/components/Input"
import { Label } from "@/components/Label"
import { Badge } from "@/components/Badge"
import { Textarea } from "@/components/Textarea"
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
  fetchPromptTemplates,
  fetchPromptTemplateDefaults,
  createPromptTemplate,
  updatePromptTemplate,
  activatePromptTemplate,
  deletePromptTemplate,
  previewPromptTemplate,
  type PromptTemplate,
  type PromptTemplateCreate,
  type PromptTemplatePreview,
} from "@/lib/api"
import {
  RiCheckLine,
  RiCloseLine,
  RiEditLine,
  RiDeleteBinLine,
  RiAddLine,
  RiFileTextLine,
  RiEyeLine,
  RiCheckboxCircleLine,
} from "@remixicon/react"

interface TemplateCardProps {
  template: PromptTemplate
  onEdit: (template: PromptTemplate) => void
  onActivate: (id: string) => Promise<void>
  onDelete: (id: string) => Promise<void>
  onPreview: (template: PromptTemplate) => void
  isAdmin: boolean
  canDelete: boolean
}

function TemplateCard({
  template,
  onEdit,
  onActivate,
  onDelete,
  onPreview,
  isAdmin,
  canDelete,
}: TemplateCardProps) {
  const [isActivating, setIsActivating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleActivate = async () => {
    setIsActivating(true)
    setError(null)
    try {
      await onActivate(template.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to activate")
    } finally {
      setIsActivating(false)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    setError(null)
    try {
      await onDelete(template.id)
      setIsDeleteDialogOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete")
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="px-4 pb-4 pt-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-950/30">
              <RiFileTextLine className="size-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                  {template.name}
                </h4>
                <Badge variant="neutral" className="text-xs">
                  {template.version}
                </Badge>
              </div>
              <p className="mt-0.5 text-xs text-gray-500">
                Updated {new Date(template.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <Badge variant={template.is_active ? "success" : "neutral"}>
            {template.is_active ? (
              <span className="flex items-center gap-1">
                <RiCheckLine className="size-3" />
                Active
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <RiCloseLine className="size-3" />
                Inactive
              </span>
            )}
          </Badge>
        </div>

        <div className="mt-4 rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
            System Prompt Preview:
          </p>
          <p className="mt-1 line-clamp-2 font-mono text-xs text-gray-500">
            {template.system_prompt.slice(0, 150)}
            {template.system_prompt.length > 150 && "..."}
          </p>
        </div>

        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-200 bg-gray-50 p-3 dark:border-gray-900 dark:bg-gray-900">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            className="h-8 px-3 text-sm"
            onClick={() => onPreview(template)}
          >
            <RiEyeLine className="mr-1 size-4" />
            Preview
          </Button>

          {isAdmin && (
            <>
              <Button
                variant="secondary"
                className="h-8 px-3 text-sm"
                onClick={() => onEdit(template)}
              >
                <RiEditLine className="mr-1 size-4" />
                Edit
              </Button>

              {!template.is_active && (
                <Button
                  variant="secondary"
                  className="h-8 px-3 text-sm"
                  onClick={handleActivate}
                  disabled={isActivating}
                >
                  <RiCheckboxCircleLine className="mr-1 size-4" />
                  {isActivating ? "Activating..." : "Activate"}
                </Button>
              )}

              {canDelete && !template.is_active && (
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
                      Delete
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Delete Template</DialogTitle>
                      <DialogDescription>
                        Are you sure you want to delete &quot;{template.name}&quot;? This
                        action cannot be undone.
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
                        disabled={isDeleting}
                      >
                        {isDeleting ? "Deleting..." : "Delete"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              )}
            </>
          )}
        </div>
      </div>
    </Card>
  )
}

interface TemplateEditorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  template?: PromptTemplate | null
  defaults?: PromptTemplatePreview | null
  onSave: (data: PromptTemplateCreate, id?: string) => Promise<void>
}

function TemplateEditorDialog({
  open,
  onOpenChange,
  template,
  defaults,
  onSave,
}: TemplateEditorDialogProps) {
  const [name, setName] = useState("")
  const [version, setVersion] = useState("v1")
  const [systemPrompt, setSystemPrompt] = useState("")
  const [userTemplate, setUserTemplate] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isEditing = !!template

  useEffect(() => {
    if (open) {
      if (template) {
        setName(template.name)
        setVersion(template.version)
        setSystemPrompt(template.system_prompt)
        setUserTemplate(template.user_template)
      } else if (defaults) {
        setName("Custom Template")
        setVersion("v1")
        setSystemPrompt(defaults.system_prompt)
        setUserTemplate(defaults.user_prompt.replace(defaults.transcript_sample, "{transcript}"))
      } else {
        setName("")
        setVersion("v1")
        setSystemPrompt("")
        setUserTemplate("")
      }
      setError(null)
    }
  }, [open, template, defaults])

  const handleSave = async () => {
    if (!name.trim()) {
      setError("Name is required")
      return
    }
    if (!systemPrompt.trim()) {
      setError("System prompt is required")
      return
    }
    if (!userTemplate.trim()) {
      setError("User template is required")
      return
    }
    if (!userTemplate.includes("{transcript}")) {
      setError("User template must contain {transcript} placeholder")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await onSave(
        {
          name: name.trim(),
          version: version.trim() || "v1",
          system_prompt: systemPrompt,
          user_template: userTemplate,
        },
        template?.id
      )
      onOpenChange(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save template")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Template" : "Create New Template"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Modify the prompt template settings below."
              : "Create a new prompt template for SPIN assessments."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="template-name" className="font-medium">
                Template Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="template-name"
                type="text"
                placeholder="e.g., Custom SPIN v2"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="template-version" className="font-medium">
                Version
              </Label>
              <Input
                id="template-version"
                type="text"
                placeholder="e.g., v1, v2"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="mt-2"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="system-prompt" className="font-medium">
              System Prompt <span className="text-red-500">*</span>
            </Label>
            <p className="mt-1 text-xs text-gray-500">
              Instructions for the LLM defining its role and behavior.
            </p>
            <Textarea
              id="system-prompt"
              placeholder="You are a senior sales coach..."
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="mt-2 min-h-[150px] font-mono text-sm"
            />
          </div>

          <div>
            <Label htmlFor="user-template" className="font-medium">
              User Template <span className="text-red-500">*</span>
            </Label>
            <p className="mt-1 text-xs text-gray-500">
              The prompt sent with each transcript. Must include{" "}
              <code className="rounded bg-gray-100 px-1 dark:bg-gray-800">
                {"{transcript}"}
              </code>{" "}
              placeholder.
            </p>
            <Textarea
              id="user-template"
              placeholder="Evaluate the following sales conversation...{transcript}"
              value={userTemplate}
              onChange={(e) => setUserTemplate(e.target.value)}
              className="mt-2 min-h-[300px] font-mono text-sm"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="secondary">Cancel</Button>
          </DialogClose>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? "Saving..." : isEditing ? "Save Changes" : "Create Template"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface PreviewDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  template: PromptTemplate | null
  preview: PromptTemplatePreview | null
  isLoading: boolean
}

function PreviewDialog({
  open,
  onOpenChange,
  template,
  preview,
  isLoading,
}: PreviewDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Preview: {template?.name || "Template"}
          </DialogTitle>
          <DialogDescription>
            See how the template renders with a sample transcript.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600" />
          </div>
        ) : preview ? (
          <div className="space-y-4 py-4">
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                System Prompt
              </h4>
              <div className="mt-2 max-h-[200px] overflow-y-auto rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
                <pre className="whitespace-pre-wrap font-mono text-xs text-gray-700 dark:text-gray-300">
                  {preview.system_prompt}
                </pre>
              </div>
            </div>

            <Divider />

            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                User Prompt (with sample transcript)
              </h4>
              <div className="mt-2 max-h-[400px] overflow-y-auto rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
                <pre className="whitespace-pre-wrap font-mono text-xs text-gray-700 dark:text-gray-300">
                  {preview.user_prompt}
                </pre>
              </div>
            </div>

            <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-950/30 dark:text-blue-400">
              <strong>Sample Transcript Used:</strong>
              <pre className="mt-2 whitespace-pre-wrap font-mono text-xs">
                {preview.transcript_sample}
              </pre>
            </div>
          </div>
        ) : (
          <p className="py-8 text-center text-gray-500">
            No preview available.
          </p>
        )}

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="secondary">Close</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function PromptTemplates() {
  const { accessToken, user } = useAuth()
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [defaults, setDefaults] = useState<PromptTemplatePreview | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Editor dialog state
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<PromptTemplate | null>(null)

  // Preview dialog state
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [previewTemplate, setPreviewTemplate] = useState<PromptTemplate | null>(null)
  const [previewData, setPreviewData] = useState<PromptTemplatePreview | null>(null)
  const [isPreviewLoading, setIsPreviewLoading] = useState(false)

  const isAdmin = user?.is_superuser ?? false

  const loadTemplates = useCallback(async () => {
    if (!accessToken) return

    try {
      setIsLoading(true)
      const [templatesData, defaultsData] = await Promise.all([
        fetchPromptTemplates(accessToken),
        fetchPromptTemplateDefaults(accessToken),
      ])
      setTemplates(templatesData)
      setDefaults(defaultsData)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load templates")
    } finally {
      setIsLoading(false)
    }
  }, [accessToken])

  useEffect(() => {
    loadTemplates()
  }, [loadTemplates])

  const handleCreate = () => {
    setEditingTemplate(null)
    setIsEditorOpen(true)
  }

  const handleEdit = (template: PromptTemplate) => {
    setEditingTemplate(template)
    setIsEditorOpen(true)
  }

  const handleSave = async (data: PromptTemplateCreate, id?: string) => {
    if (!accessToken) return

    if (id) {
      await updatePromptTemplate(id, data, accessToken)
    } else {
      await createPromptTemplate(data, accessToken)
    }
    await loadTemplates()
  }

  const handleActivate = async (id: string) => {
    if (!accessToken) return
    await activatePromptTemplate(id, accessToken)
    await loadTemplates()
  }

  const handleDelete = async (id: string) => {
    if (!accessToken) return
    await deletePromptTemplate(id, accessToken)
    await loadTemplates()
  }

  const handlePreview = async (template: PromptTemplate) => {
    setPreviewTemplate(template)
    setIsPreviewOpen(true)
    setIsPreviewLoading(true)

    try {
      const preview = await previewPromptTemplate(
        {
          name: template.name,
          version: template.version,
          system_prompt: template.system_prompt,
          user_template: template.user_template,
        },
        accessToken
      )
      setPreviewData(preview)
    } catch (e) {
      console.error("Failed to load preview:", e)
      setPreviewData(null)
    } finally {
      setIsPreviewLoading(false)
    }
  }

  const activeTemplate = templates.find((t) => t.is_active)
  const canDeleteTemplates = templates.length > 1

  return (
    <>
      <div className="space-y-10">
        <section aria-labelledby="prompt-templates-overview">
          <div className="grid grid-cols-1 gap-x-14 gap-y-8 md:grid-cols-3">
            <div>
              <h2
                id="prompt-templates-overview"
                className="scroll-mt-10 font-semibold text-gray-900 dark:text-gray-50"
              >
                Prompt Templates
              </h2>
              <p className="mt-1 text-sm leading-6 text-gray-500">
                Customize the prompts used for SPIN sales assessments. Each
                organization has its own templates.
              </p>
              <div className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/30 dark:text-amber-400">
                <strong>Note:</strong> Only one template can be active at a
                time. The active template is used for all new assessments.
              </div>
            </div>
            <div className="md:col-span-2">
              <div className="mb-6 flex items-center justify-between rounded-lg bg-gray-50 p-4 dark:bg-gray-900">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
                    Active Template
                  </p>
                  <p className="text-sm text-gray-500">
                    {activeTemplate ? (
                      <>
                        {activeTemplate.name}{" "}
                        <span className="text-gray-400">
                          ({activeTemplate.version})
                        </span>
                      </>
                    ) : (
                      "No active template"
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {activeTemplate ? (
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
                  {isAdmin && (
                    <Button
                      variant="primary"
                      className="ml-2 h-8 px-3 text-sm"
                      onClick={handleCreate}
                    >
                      <RiAddLine className="mr-1 size-4" />
                      New Template
                    </Button>
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
              ) : templates.length === 0 ? (
                <div className="rounded-lg border-2 border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
                  <RiFileTextLine className="mx-auto size-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-50">
                    No templates yet
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Create your first prompt template to get started.
                  </p>
                  {isAdmin && (
                    <Button
                      variant="primary"
                      className="mt-4"
                      onClick={handleCreate}
                    >
                      <RiAddLine className="mr-1 size-4" />
                      Create Template
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {templates.map((template) => (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      onEdit={handleEdit}
                      onActivate={handleActivate}
                      onDelete={handleDelete}
                      onPreview={handlePreview}
                      isAdmin={isAdmin}
                      canDelete={canDeleteTemplates}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        <Divider />

        <section aria-labelledby="template-tips">
          <div className="grid grid-cols-1 gap-x-14 gap-y-8 md:grid-cols-3">
            <div>
              <h2
                id="template-tips"
                className="scroll-mt-10 font-semibold text-gray-900 dark:text-gray-50"
              >
                Template Tips
              </h2>
              <p className="mt-1 text-sm leading-6 text-gray-500">
                Best practices for effective prompt templates.
              </p>
            </div>
            <div className="md:col-span-2">
              <Card className="p-4">
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Include scoring rubric:
                      </strong>{" "}
                      Define clear 1-5 scales for each dimension to ensure
                      consistent scoring.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Specify JSON schema:
                      </strong>{" "}
                      Include the expected JSON structure in the user template
                      for reliable output.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Use {"{transcript}"} placeholder:
                      </strong>{" "}
                      This is where the sales conversation will be injected.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Preview before activating:
                      </strong>{" "}
                      Always preview your template with a sample transcript
                      before making it active.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Version your templates:
                      </strong>{" "}
                      Use version numbers (v1, v2) to track changes and compare
                      results.
                    </span>
                  </li>
                </ul>
              </Card>
            </div>
          </div>
        </section>
      </div>

      <TemplateEditorDialog
        open={isEditorOpen}
        onOpenChange={setIsEditorOpen}
        template={editingTemplate}
        defaults={defaults}
        onSave={handleSave}
      />

      <PreviewDialog
        open={isPreviewOpen}
        onOpenChange={setIsPreviewOpen}
        template={previewTemplate}
        preview={previewData}
        isLoading={isPreviewLoading}
      />
    </>
  )
}



