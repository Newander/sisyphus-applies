import { getPrompts } from "@/lib/api";

import { PromptsEditor } from "./prompts-editor";

export default async function PromptsPage() {
  const prompts = await getPrompts();

  return (
    <main className="min-h-screen bg-background">
      <PromptsEditor initialPrompts={prompts} />
    </main>
  );
}
