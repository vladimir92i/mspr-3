import type { Metadata } from "next";
import "./globals.css";
import Navbar from "./components/Navbar";

export const metadata: Metadata = {
  title: "Obrail App",
  description: "Site pour explorer les données de Obrail !",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="font-sans min-h-full flex flex-col">
        <Navbar></Navbar>
        <main className="flex-1 bg-gray-100 ">{children}</main>
      </body>
    </html>
  );
}
