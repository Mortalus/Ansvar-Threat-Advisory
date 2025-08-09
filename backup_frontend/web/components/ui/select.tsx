import * as React from "react"
import { cn } from "@/lib/utils"

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  onValueChange?: (value: string) => void
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, onValueChange, onChange, ...props }, ref) => {
    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      onChange?.(e)
      onValueChange?.(e.target.value)
    }

    return (
      <select
        className={cn(
          "flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        onChange={handleChange}
        {...props}
      >
        {children}
      </select>
    )
  }
)
Select.displayName = "Select"

// Add missing Select sub-components as aliases for compatibility
const SelectTrigger = Select
const SelectValue = ({ children, placeholder, ...props }: any) => <span {...props}>{children || placeholder}</span>
const SelectContent = ({ children, ...props }: any) => <>{children}</>
const SelectItem = ({ children, value, ...props }: any) => <option value={value} {...props}>{children}</option>

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }