"use client"

import { Button } from "@/components/Button"
import { cx, focusRing } from "@/lib/utils"
import { RiMore2Fill } from "@remixicon/react"
import { useAuth } from "@/app/auth/AuthContext"

import { DropdownUserProfile } from "./DropdownUserProfile"

/**
 * Generate user initials from full name or email
 * @param fullName - User's full name (e.g., "John Doe")
 * @param email - User's email (e.g., "john@example.com")
 * @returns Two-letter initials in uppercase (e.g., "JD" or "JO")
 */
function getUserInitials(fullName: string | null, email: string): string {
  if (fullName && fullName.trim()) {
    const parts = fullName.trim().split(/\s+/)
    if (parts.length >= 2) {
      // Use first letter of first and last name
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    }
    // Single name: use first two letters
    return fullName.slice(0, 2).toUpperCase()
  }
  // Fallback to email: use first two letters
  return email.slice(0, 2).toUpperCase()
}

/**
 * Get display name for user
 * @param fullName - User's full name
 * @param email - User's email
 * @returns Full name if available, otherwise email
 */
function getDisplayName(fullName: string | null, email: string): string {
  return fullName && fullName.trim() ? fullName : email
}

export const UserProfileDesktop = () => {
  const { user, email, isLoading } = useAuth()

  // While loading or if no user data, show placeholder
  if (isLoading || !user || !email) {
    return (
      <DropdownUserProfile>
        <Button
          aria-label="User settings"
          variant="ghost"
          className={cx(
            focusRing,
            "group flex w-full items-center justify-between rounded-md p-2 text-sm font-medium text-gray-900 hover:bg-gray-100 data-[state=open]:bg-gray-100 data-[state=open]:bg-gray-400/10 hover:dark:bg-gray-400/10",
          )}
        >
          <span className="flex items-center gap-3">
            <span
              className="flex size-8 shrink-0 items-center justify-center rounded-full border border-gray-300 bg-white text-xs text-gray-700 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300"
              aria-hidden="true"
            >
              ...
            </span>
            <span className="text-gray-400">Loading...</span>
          </span>
          <RiMore2Fill
            className="size-4 shrink-0 text-gray-500 group-hover:text-gray-700 group-hover:dark:text-gray-400"
            aria-hidden="true"
          />
        </Button>
      </DropdownUserProfile>
    )
  }

  const initials = getUserInitials(user.full_name, email)
  const displayName = getDisplayName(user.full_name, email)

  return (
    <DropdownUserProfile>
      <Button
        aria-label="User settings"
        variant="ghost"
        className={cx(
          focusRing,
          "group flex w-full items-center justify-between rounded-md p-2 text-sm font-medium text-gray-900 hover:bg-gray-100 data-[state=open]:bg-gray-100 data-[state=open]:bg-gray-400/10 hover:dark:bg-gray-400/10",
        )}
      >
        <span className="flex items-center gap-3">
          <span
            className="flex size-8 shrink-0 items-center justify-center rounded-full border border-gray-300 bg-white text-xs text-gray-700 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300"
            aria-hidden="true"
          >
            {initials}
          </span>
          <span>{displayName}</span>
        </span>
        <RiMore2Fill
          className="size-4 shrink-0 text-gray-500 group-hover:text-gray-700 group-hover:dark:text-gray-400"
          aria-hidden="true"
        />
      </Button>
    </DropdownUserProfile>
  )
}

export const UserProfileMobile = () => {
  const { user, email, isLoading } = useAuth()

  // While loading or if no user data, show placeholder
  if (isLoading || !user || !email) {
    return (
      <DropdownUserProfile align="end">
        <Button
          aria-label="User settings"
          variant="ghost"
          className={cx(
            "group flex items-center rounded-md p-1 text-sm font-medium text-gray-900 hover:bg-gray-100 data-[state=open]:bg-gray-100 data-[state=open]:bg-gray-400/10 hover:dark:bg-gray-400/10",
          )}
        >
          <span
            className="flex size-7 shrink-0 items-center justify-center rounded-full border border-gray-300 bg-white text-xs text-gray-700 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300"
            aria-hidden="true"
          >
            ...
          </span>
        </Button>
      </DropdownUserProfile>
    )
  }

  const initials = getUserInitials(user.full_name, email)

  return (
    <DropdownUserProfile align="end">
      <Button
        aria-label="User settings"
        variant="ghost"
        className={cx(
          "group flex items-center rounded-md p-1 text-sm font-medium text-gray-900 hover:bg-gray-100 data-[state=open]:bg-gray-100 data-[state=open]:bg-gray-400/10 hover:dark:bg-gray-400/10",
        )}
      >
        <span
          className="flex size-7 shrink-0 items-center justify-center rounded-full border border-gray-300 bg-white text-xs text-gray-700 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300"
          aria-hidden="true"
        >
          {initials}
        </span>
      </Button>
    </DropdownUserProfile>
  )
}
