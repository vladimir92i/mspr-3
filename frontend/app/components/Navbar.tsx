"use client";

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { TrainFront } from "lucide-react";
import { cn } from "@/app/lib/utils"; // Utilitaire classique pour fusionner les classes

const NAV_LINKS = [
  { name: "Trajets", href: "/" },
  { name: "Statistiques", href: "/statistiques" },
  { name: "Supervision", href: "/supervision" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav
      role="navigation"
      aria-label="Menu principal"
      className="flex flex-row px-8 py-4 bg-white border-b border-gray-200"
    >
      {/* Logo et Nom */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-600 rounded-lg text-white">
          <TrainFront size={24} aria-hidden="true" />
        </div>
        <span className="text-xl font-bold text-slate-900 tracking-tight">
          ObRail <span className="text-blue-600">Europe</span>
        </span>
      </div>
      {/* Liens de Navigation */}
      <NavigationMenu className="pl-24">
        <NavigationMenuList className="gap-2">
          {/* On réduit le gap car les boutons ont du padding interne */}
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;

            return (
              <NavigationMenuItem key={link.href}>
                {/* On ajoute 'asChild' sur NavigationMenuLink 
                  Cela lui dit : "ne crée pas de <a>, utilise celui de mon enfant" */}
                <NavigationMenuLink asChild active={isActive}>
                  <Link
                    href={link.href}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      navigationMenuTriggerStyle(),
                      "text-sm font-medium transition-all",
                      isActive ? "bg-blue-50 text-blue-600 focus:bg-blue-50 focus:text-blue-600" : "text-slate-600",
                    )}
                  >
                    {link.name}
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            );
          })}
        </NavigationMenuList>
      </NavigationMenu>
    </nav>
  );
}
