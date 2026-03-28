import React, { useEffect } from "react";
import { useLocation } from "wouter";

// Simple redirect to the upload page
export default function Home() {
  const [, setLocation] = useLocation();

  useEffect(() => {
    setLocation("/upload");
  }, [setLocation]);

  return null;
}
