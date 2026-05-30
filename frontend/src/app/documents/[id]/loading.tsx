import { AppNav } from "@/components/app-nav";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function DocumentLoading() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
        <header className="flex flex-col gap-4 rounded-lg border-l-4 border-primary bg-muted p-5">
          <AppNav active="documents" />
          <div className="flex flex-col gap-2">
            <div className="h-5 w-36 rounded-md bg-muted-foreground/20" />
            <div className="h-9 w-full max-w-xl rounded-md bg-muted-foreground/20" />
          </div>
        </header>

        <Card>
          <CardHeader>
            <div className="flex items-start gap-3">
              <div className="size-6 rounded-md bg-muted-foreground/20" />
              <div className="flex min-w-0 flex-1 flex-col gap-2">
                <div className="h-5 w-full max-w-md rounded-md bg-muted-foreground/20" />
                <div className="h-4 w-full max-w-2xl rounded-md bg-muted-foreground/20" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 md:grid-cols-3">
              {[0, 1, 2].map((item) => (
                <div className="rounded-md border p-4" key={item}>
                  <div className="h-4 w-16 rounded-md bg-muted-foreground/20" />
                  <div className="mt-3 h-5 w-24 rounded-md bg-muted-foreground/20" />
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
