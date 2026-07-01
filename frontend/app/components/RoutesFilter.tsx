"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/app/lib/utils";

const FILTERS = [
  { id: "all", label: "Toutes les routes" },
  { id: "day", label: "Trains de jour" },
  { id: "night", label: "Trains de nuit" },
];

interface RouteFiltersProps {
  onFilterChange: (filterId: string) => void;
}

export default function RouteFilters({ onFilterChange }: RouteFiltersProps) {
  const [activeFilter, setActiveFilter] = useState("all");

  const handleFilterClick = (filterId: string) => {
    setActiveFilter(filterId);
    onFilterChange(filterId);
  };

  return (
    <div className="flex gap-3 items-center">
      {FILTERS.map((filter) => {
        const isSelected = activeFilter === filter.id;

        return (
          <Button
            key={filter.id}
            onClick={() => handleFilterClick(filter.id)}
            variant={isSelected ? "default" : "outline"}
            className={cn(
              "rounded-full px-5 h-9 text-xs font-medium transition-all",
              isSelected
                ? "bg-slate-900 text-white hover:bg-slate-800"
                : "border-slate-200 text-slate-600 hover:bg-slate-50",
            )}
          >
            {filter.label}
          </Button>
        );
      })}
    </div>
  );
}
