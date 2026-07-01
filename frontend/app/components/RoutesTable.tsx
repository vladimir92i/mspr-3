import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Field, FieldLabel } from "@/components/ui/field";
import { Trip } from "../types/routes";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { formatDuration } from "@/app/lib/utils";
import { useState, useMemo } from "react";
import { extractHour } from "@/app/lib/utils";

export default function RoutesTable({ routes }: { routes: Trip[] }) {
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(25);

  const totalPages = Math.ceil(routes.length / perPage);
  const paginatedRoutes = useMemo(() => {
    const start = (currentPage - 1) * perPage;
    const end = start + perPage;
    return routes.slice(start, end);
  }, [routes, currentPage, perPage]);

  const handlePerPageChange = (value: string) => {
    setPerPage(Number(value));
    setCurrentPage(1); // Réinitialiser à la page 1
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };
  return (
    <Table className="shadow-xl inset-shadow-xs bg-white">
      <TableCaption>La liste de toutes nos routes en bdd.</TableCaption>
      <TableHeader className="w-full bg-[#767676]">
        <TableRow>
          <TableHead className="" scope="col">
            Nom du trajet
          </TableHead>
          <TableHead className="w-1/6" scope="col">
            Depart→ Arrive
          </TableHead>
          <TableHead className="w-2/6" scope="col">
            Type
          </TableHead>
          <TableHead className="w-2/6" scope="col">
            Operateur
          </TableHead>
          <TableHead className="w-3/6" scope="col">
            Durée
          </TableHead>
          <TableHead className="w-3/6" scope="col">
            Co2 économisés
          </TableHead>
          <TableHead className="text-right!" scope="col">
            Voir le trajet
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody className="w-full ">
        {paginatedRoutes.map((route) => {
          const departureHour = extractHour(route.departure_time);
          const isNight = departureHour >= 22 || departureHour < 6;

          return (
            <TableRow key={route.id_trip}>
              <TableCell>{route.name}</TableCell>
              <TableCell>
                {route.origin} → {route.destination}
              </TableCell>
              <TableCell>
                <Badge
                  className={
                    isNight
                      ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border-indigo-200" // Style Nuit
                      : "bg-orange-50 text-orange-700 hover:bg-orange-100 border-orange-200" // Style Jour
                  }
                >
                  {isNight ? (
                    <>
                      <span aria-hidden>🌙</span> Nuit
                      <span className="sr-only">Type: Nuit</span>
                    </>
                  ) : (
                    <>
                      <span aria-hidden>☀️</span> Jour
                      <span className="sr-only">Type: Jour</span>
                    </>
                  )}
                </Badge>
              </TableCell>
              <TableCell>{route.agency_name ?? `Opérateur ${route.id_agency}`}</TableCell>
              <TableCell>{formatDuration(route.duration)}</TableCell>
              <TableCell className=" text-green-500">🍃{(route.distance * 0.255).toFixed(2)} kg</TableCell>
              <TableCell className="text-right!">
                <Button className="rounded-full" asChild aria-label="Voir le trajet">
                  <Link href={`/trajet/${route.id_trip}`}>
                    <span aria-hidden>Voir</span>
                    <span className="sr-only">Voir le trajet</span>
                  </Link>
                </Button>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
      <TableFooter>
        <TableRow>
          <TableCell colSpan={6}>
            <Field orientation="horizontal" className="w-fit">
              <FieldLabel htmlFor="select-rows-per-page">Route par page</FieldLabel>
              <Select value={perPage.toString()} onValueChange={handlePerPageChange}>
                <SelectTrigger className="w-20" id="select-rows-per-page">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent align="start">
                  <SelectGroup>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="25">25</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                  </SelectGroup>
                </SelectContent>
              </Select>
            </Field>
          </TableCell>
          <TableCell className="text-right">
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      handlePageChange(currentPage - 1);
                    }}
                  />
                </PaginationItem>

                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => i + 1).map((page) => (
                  <PaginationItem key={page}>
                    <PaginationLink
                      href="#"
                      isActive={currentPage === page}
                      onClick={(e) => {
                        e.preventDefault();
                        handlePageChange(page);
                      }}
                    >
                      {page}
                    </PaginationLink>
                  </PaginationItem>
                ))}

                {totalPages > 5 && (
                  <PaginationItem>
                    <PaginationEllipsis />
                  </PaginationItem>
                )}

                <PaginationItem>
                  <PaginationNext
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      handlePageChange(currentPage + 1);
                    }}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </TableCell>
        </TableRow>
      </TableFooter>
    </Table>
  );
}
