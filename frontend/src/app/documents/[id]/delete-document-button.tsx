"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { deleteDocument } from "@/lib/api";

type DeleteDocumentButtonProps = {
  documentId: string;
  documentName: string;
};

export function DeleteDocumentButton({ documentId, documentName }: DeleteDocumentButtonProps) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);

  async function handleDelete() {
    const confirmed = window.confirm(`Удалить файл "${documentName}" в корзину?`);
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteDocument(documentId);
      router.push("/documents");
      router.refresh();
    } catch {
      window.alert("Не удалось отправить файл в корзину.");
      setIsDeleting(false);
    }
  }

  return (
    <Button
      disabled={isDeleting}
      onClick={handleDelete}
      size="sm"
      type="button"
      variant="destructive"
    >
      {isDeleting ? "Удаление..." : "Удалить"}
    </Button>
  );
}
