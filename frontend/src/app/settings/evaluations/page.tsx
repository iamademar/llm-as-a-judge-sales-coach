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
  fetchEvaluationDatasets,
  fetchPromptTemplates,
  fetchTemplateEvaluations,
  createEvaluationDataset,
  updateEvaluationDataset,
  deleteEvaluationDataset,
  runEvaluation,
  type EvaluationDataset,
  type EvaluationDatasetCreate,
  type EvaluationRun,
  type PromptTemplate,
} from "@/lib/api"
import {
  RiDatabase2Line,
  RiPlayLine,
  RiEditLine,
  RiDeleteBinLine,
  RiAddLine,
  RiCheckLine,
  RiBarChartBoxLine,
  RiTimeLine,
} from "@remixicon/react"

interface DatasetCardProps {
  dataset: EvaluationDataset
  templates: PromptTemplate[]
  onEdit: (dataset: EvaluationDataset) => void
  onDelete: (id: string) => Promise<void>
  onRunEval: (dataset: EvaluationDataset) => void
  onViewRuns: (dataset: EvaluationDataset) => void
  isAdmin: boolean
}

function DatasetCard({
  dataset,
  templates,
  onEdit,
  onDelete,
  onRunEval,
  onViewRuns,
  isAdmin,
}: DatasetCardProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    setIsDeleting(true)
    setError(null)
    try {
      await onDelete(dataset.id)
      setIsDeleteDialogOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete")
    } finally {
      setIsDeleting(false)
    }
  }

  const sourceTypeColors = {
    csv: "bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-400",
    langsmith: "bg-purple-50 dark:bg-purple-950/30 text-purple-700 dark:text-purple-400",
    database: "bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400",
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="px-4 pb-4 pt-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-950/30">
              <RiDatabase2Line className="size-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                  {dataset.name}
                </h4>
                <Badge variant="neutral" className={sourceTypeColors[dataset.source_type]}>
                  {dataset.source_type}
                </Badge>
              </div>
              <p className="mt-0.5 text-xs text-gray-500">
                {dataset.num_examples} examples • Created{" "}
                {new Date(dataset.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {dataset.description && (
          <div className="mt-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
            <p className="text-xs text-gray-600 dark:text-gray-400">
              {dataset.description}
            </p>
          </div>
        )}

        {dataset.source_path && (
          <div className="mt-2">
            <p className="text-xs text-gray-500">
              <span className="font-medium">Source:</span> {dataset.source_path}
            </p>
          </div>
        )}

        {dataset.langsmith_dataset_name && (
          <div className="mt-2 flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
            <RiCheckLine className="h-3 w-3" />
            Synced to LangSmith as: {dataset.langsmith_dataset_name}
          </div>
        )}

        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-200 bg-gray-50 p-3 dark:border-gray-900 dark:bg-gray-900">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            className="h-8 px-3 text-sm"
            onClick={() => onViewRuns(dataset)}
          >
            <RiBarChartBoxLine className="mr-1 size-4" />
            View Runs
          </Button>

          {isAdmin && templates.length > 0 && (
            <Button
              variant="primary"
              className="h-8 px-3 text-sm"
              onClick={() => onRunEval(dataset)}
            >
              <RiPlayLine className="mr-1 size-4" />
              Run Evaluation
            </Button>
          )}

          {isAdmin && (
            <>
              <Button
                variant="secondary"
                className="h-8 px-3 text-sm"
                onClick={() => onEdit(dataset)}
              >
                <RiEditLine className="mr-1 size-4" />
                Edit
              </Button>

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
                    <DialogTitle>Delete Dataset</DialogTitle>
                    <DialogDescription>
                      Are you sure you want to delete &quot;{dataset.name}&quot;?
                      This will not delete associated evaluation runs.
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
            </>
          )}
        </div>
      </div>
    </Card>
  )
}

interface DatasetEditorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dataset?: EvaluationDataset | null
  onSave: (data: EvaluationDatasetCreate, id?: string) => Promise<void>
}

function DatasetEditorDialog({
  open,
  onOpenChange,
  dataset,
  onSave,
}: DatasetEditorDialogProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isEditing = !!dataset

  useEffect(() => {
    if (open) {
      if (dataset) {
        setName(dataset.name)
        setDescription(dataset.description || "")
        setFile(null)
      } else {
        setName("")
        setDescription("")
        setFile(null)
      }
      setError(null)
    }
  }, [open, dataset])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError("File must be a CSV")
        setFile(null)
        return
      }
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleSave = async () => {
    if (!name.trim()) {
      setError("Name is required")
      return
    }
    
    if (!isEditing && !file) {
      setError("Please select a CSV file")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await onSave(
        {
          name: name.trim(),
          description: description.trim() || undefined,
          file: file!,
        },
        dataset?.id
      )
      onOpenChange(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save dataset")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Dataset" : "Create Evaluation Dataset"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update the evaluation dataset details."
              : "Create a new golden dataset for evaluating prompts."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div>
            <Label htmlFor="dataset-name" className="font-medium">
              Dataset Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="dataset-name"
              type="text"
              placeholder="e.g., Q4 2024 Golden Set"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-2"
            />
          </div>

          <div>
            <Label htmlFor="dataset-description" className="font-medium">
              Description
            </Label>
            <Textarea
              id="dataset-description"
              placeholder="Describe this dataset..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-2"
            />
          </div>

          {!isEditing && (
            <div>
              <Label htmlFor="csv-file" className="font-medium">
                CSV File <span className="text-red-500">*</span>
              </Label>
              <input
                id="csv-file"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="mt-2 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100 dark:border-gray-700 dark:bg-gray-950 dark:file:bg-indigo-950/30 dark:file:text-indigo-400"
              />
              <p className="mt-1 text-xs text-gray-500">
                CSV with columns: id, transcript, score_situation, score_problem, score_implication, score_need_payoff, score_flow, score_tone, score_engagement
              </p>
              {file && (
                <p className="mt-2 text-sm text-green-600 dark:text-green-400">
                  Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>
          )}

          {isEditing && (
            <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/30 dark:text-amber-400">
              <strong>Note:</strong> File cannot be changed when editing. To use a different file, create a new dataset.
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="secondary">Cancel</Button>
          </DialogClose>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? "Saving..." : isEditing ? "Save Changes" : "Create Dataset"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface RunEvaluationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dataset: EvaluationDataset | null
  templates: PromptTemplate[]
  onRun: (templateId: string, datasetId: string, experimentName?: string) => Promise<void>
}

function RunEvaluationDialog({
  open,
  onOpenChange,
  dataset,
  templates,
  onRun,
}: RunEvaluationDialogProps) {
  const [templateId, setTemplateId] = useState("")
  const [experimentName, setExperimentName] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      const activeTemplate = templates.find((t) => t.is_active)
      setTemplateId(activeTemplate?.id || "")
      setExperimentName("")
      setError(null)
    }
  }, [open, templates])

  const handleRun = async () => {
    if (!templateId || !dataset) {
      setError("Please select a template")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await onRun(templateId, dataset.id, experimentName.trim() || undefined)
      onOpenChange(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run evaluation")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Run Evaluation</DialogTitle>
          <DialogDescription>
            Evaluate a prompt template against {dataset?.name}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div>
            <Label htmlFor="template-select" className="font-medium">
              Prompt Template <span className="text-red-500">*</span>
            </Label>
            <select
              id="template-select"
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
              className="mt-2 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-950"
            >
              <option value="">Select a template...</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name} ({template.version})
                  {template.is_active ? " - Active" : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <Label htmlFor="experiment-name" className="font-medium">
              Experiment Name (optional)
            </Label>
            <Input
              id="experiment-name"
              type="text"
              placeholder="e.g., improved-implication-v2"
              value={experimentName}
              onChange={(e) => setExperimentName(e.target.value)}
              className="mt-2"
            />
            <p className="mt-1 text-xs text-gray-500">
              Use a name to track different versions or experiments
            </p>
          </div>

          {error && (
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          )}

          <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950/30 dark:text-amber-400">
            <strong>Note:</strong> This will run {dataset?.num_examples || 0}{" "}
            evaluations and may take several minutes.
          </div>
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="secondary">Cancel</Button>
          </DialogClose>
          <Button onClick={handleRun} disabled={isLoading}>
            {isLoading ? "Running..." : "Run Evaluation"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface EvaluationRunsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dataset: EvaluationDataset | null
  templates: PromptTemplate[]
  accessToken: string | null
}

function EvaluationRunsDialog({
  open,
  onOpenChange,
  dataset,
  templates,
  accessToken,
}: EvaluationRunsDialogProps) {
  const [runs, setRuns] = useState<EvaluationRun[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open && dataset) {
      loadRuns()
    }
  }, [open, dataset])

  const loadRuns = async () => {
    if (!dataset || !accessToken) return

    setIsLoading(true)
    setError(null)

    try {
      // For now, fetch runs for all templates and filter by dataset
      // This is a workaround since we don't have a dedicated endpoint yet
      const templatePromises = templates.map(t => 
        fetchTemplateEvaluations(t.id, accessToken).catch(() => [])
      )
      const allRuns = await Promise.all(templatePromises)
      const flatRuns = allRuns.flat()
      const datasetRuns = flatRuns.filter(run => run.dataset_id === dataset.id)
      setRuns(datasetRuns.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ))
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load runs")
    } finally {
      setIsLoading(false)
    }
  }

  const getTemplateName = (templateId: string) => {
    const template = templates.find((t) => t.id === templateId)
    return template ? `${template.name} (${template.version})` : "Unknown"
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Evaluation Runs: {dataset?.name}</DialogTitle>
          <DialogDescription>
            View all evaluation runs for this dataset
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600" />
            </div>
          ) : error ? (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-400">
              {error}
            </div>
          ) : runs.length === 0 ? (
            <div className="rounded-lg border-2 border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
              <RiBarChartBoxLine className="mx-auto size-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-50">
                No evaluation runs yet
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Run an evaluation to see results here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {runs.map((run) => (
                <Card key={run.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                          {run.experiment_name || "Unnamed Experiment"}
                        </h4>
                        <Badge variant="neutral" className="text-xs">
                          {run.model_name}
                        </Badge>
                        {run.langsmith_url && (
                          <a
                            href={run.langsmith_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 hover:underline"
                          >
                            View in LangSmith
                            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        Template: {getTemplateName(run.prompt_template_id)}
                      </p>
                      <p className="text-xs text-gray-500">
                        <RiTimeLine className="mr-1 inline size-3" />
                        {new Date(run.created_at).toLocaleString()} •{" "}
                        {run.runtime_seconds?.toFixed(1)}s
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                        QWK: {run.macro_qwk?.toFixed(3) || "N/A"}
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        Pearson: {run.macro_pearson_r?.toFixed(3) || "N/A"}
                      </div>
                      <div className="text-xs text-gray-500">
                        ±1: {run.macro_plus_minus_one?.toFixed(3) || "N/A"}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="secondary">Close</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function Evaluations() {
  const { accessToken, user } = useAuth()
  const [datasets, setDatasets] = useState<EvaluationDataset[]>([])
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Editor dialog state
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [editingDataset, setEditingDataset] = useState<EvaluationDataset | null>(null)

  // Run evaluation dialog state
  const [isRunDialogOpen, setIsRunDialogOpen] = useState(false)
  const [runningDataset, setRunningDataset] = useState<EvaluationDataset | null>(null)

  // Runs dialog state
  const [isRunsDialogOpen, setIsRunsDialogOpen] = useState(false)
  const [viewingDataset, setViewingDataset] = useState<EvaluationDataset | null>(null)

  const isAdmin = user?.is_superuser ?? false

  const loadData = useCallback(async () => {
    if (!accessToken) return

    try {
      setIsLoading(true)
      const [datasetsData, templatesData] = await Promise.all([
        fetchEvaluationDatasets(accessToken),
        fetchPromptTemplates(accessToken),
      ])
      setDatasets(datasetsData)
      setTemplates(templatesData)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data")
    } finally {
      setIsLoading(false)
    }
  }, [accessToken])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCreate = () => {
    setEditingDataset(null)
    setIsEditorOpen(true)
  }

  const handleEdit = (dataset: EvaluationDataset) => {
    setEditingDataset(dataset)
    setIsEditorOpen(true)
  }

  const handleSave = async (data: EvaluationDatasetCreate, id?: string) => {
    if (!accessToken) return

    if (id) {
      // When editing, only update name and description (file cannot be changed)
      await updateEvaluationDataset(id, {
        name: data.name,
        description: data.description,
      }, accessToken)
    } else {
      // When creating, upload file
      await createEvaluationDataset(data, accessToken)
    }
    await loadData()
  }

  const handleDelete = async (id: string) => {
    if (!accessToken) return
    await deleteEvaluationDataset(id, accessToken)
    await loadData()
  }

  const handleRunEval = (dataset: EvaluationDataset) => {
    setRunningDataset(dataset)
    setIsRunDialogOpen(true)
  }

  const handleRunEvaluation = async (
    templateId: string,
    datasetId: string,
    experimentName?: string
  ) => {
    if (!accessToken) return
    await runEvaluation(
      {
        prompt_template_id: templateId,
        dataset_id: datasetId,
        experiment_name: experimentName,
      },
      accessToken
    )
    await loadData()
  }

  const handleViewRuns = (dataset: EvaluationDataset) => {
    setViewingDataset(dataset)
    setIsRunsDialogOpen(true)
  }

  return (
    <>
      <div className="space-y-10">
        <section aria-labelledby="evaluations-overview">
          <div className="grid grid-cols-1 gap-x-14 gap-y-8 md:grid-cols-3">
            <div>
              <h2
                id="evaluations-overview"
                className="scroll-mt-10 font-semibold text-gray-900 dark:text-gray-50"
              >
                Evaluation Datasets
              </h2>
              <p className="mt-1 text-sm leading-6 text-gray-500">
                Manage golden datasets for evaluating prompt templates. Track
                metrics like Pearson correlation, QWK, and accuracy.
              </p>
              <div className="mt-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-950/30 dark:text-blue-400">
                <strong>Tip:</strong> Use evaluation datasets to measure prompt
                performance and iterate on improvements.
              </div>
            </div>
            <div className="md:col-span-2">
              <div className="mb-6 flex items-center justify-between rounded-lg bg-gray-50 p-4 dark:bg-gray-900">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
                    Total Datasets
                  </p>
                  <p className="text-sm text-gray-500">
                    {datasets.length} dataset{datasets.length !== 1 ? "s" : ""}{" "}
                    available
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {templates.length > 0 ? (
                    <Badge variant="success">
                      <RiCheckLine className="mr-1 size-3" />
                      {templates.length} template{templates.length !== 1 ? "s" : ""}
                    </Badge>
                  ) : (
                    <Badge variant="warning">No templates</Badge>
                  )}
                  {isAdmin && (
                    <Button
                      variant="primary"
                      className="ml-2 h-8 px-3 text-sm"
                      onClick={handleCreate}
                    >
                      <RiAddLine className="mr-1 size-4" />
                      New Dataset
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
              ) : datasets.length === 0 ? (
                <div className="rounded-lg border-2 border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
                  <RiDatabase2Line className="mx-auto size-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-50">
                    No evaluation datasets yet
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Create your first dataset to start evaluating prompts.
                  </p>
                  {isAdmin && (
                    <Button
                      variant="primary"
                      className="mt-4"
                      onClick={handleCreate}
                    >
                      <RiAddLine className="mr-1 size-4" />
                      Create Dataset
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {datasets.map((dataset) => (
                    <DatasetCard
                      key={dataset.id}
                      dataset={dataset}
                      templates={templates}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                      onRunEval={handleRunEval}
                      onViewRuns={handleViewRuns}
                      isAdmin={isAdmin}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        <Divider />

        <section aria-labelledby="evaluation-tips">
          <div className="grid grid-cols-1 gap-x-14 gap-y-8 md:grid-cols-3">
            <div>
              <h2
                id="evaluation-tips"
                className="scroll-mt-10 font-semibold text-gray-900 dark:text-gray-50"
              >
                Evaluation Guide
              </h2>
              <p className="mt-1 text-sm leading-6 text-gray-500">
                Best practices for effective prompt evaluation.
              </p>
            </div>
            <div className="md:col-span-2">
              <Card className="p-4">
                <ul className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Create golden datasets:
                      </strong>{" "}
                      Collect 50-100 transcripts with expert-labeled scores
                      for reliable metrics.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Track experiments:
                      </strong>{" "}
                      Use descriptive experiment names to compare different
                      prompt iterations.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Focus on QWK:
                      </strong>{" "}
                      Quadratic Weighted Kappa is most robust for ordinal
                      scores. Aim for &gt; 0.6.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <RiCheckLine className="mt-0.5 size-4 shrink-0 text-green-600" />
                    <span>
                      <strong className="text-gray-900 dark:text-gray-100">
                        Iterate systematically:
                      </strong>{" "}
                      Run baseline, modify prompt, re-evaluate, and compare
                      metrics.
                    </span>
                  </li>
                </ul>
              </Card>
            </div>
          </div>
        </section>
      </div>

      <DatasetEditorDialog
        open={isEditorOpen}
        onOpenChange={setIsEditorOpen}
        dataset={editingDataset}
        onSave={handleSave}
      />

      <RunEvaluationDialog
        open={isRunDialogOpen}
        onOpenChange={setIsRunDialogOpen}
        dataset={runningDataset}
        templates={templates}
        onRun={handleRunEvaluation}
      />

      <EvaluationRunsDialog
        open={isRunsDialogOpen}
        onOpenChange={setIsRunsDialogOpen}
        dataset={viewingDataset}
        templates={templates}
        accessToken={accessToken}
      />
    </>
  )
}

