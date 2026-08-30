import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-12 sm:px-10">
      <section className="mx-auto flex min-h-[calc(100vh-6rem)] max-w-5xl flex-col justify-between rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200 sm:p-12">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-accent font-bold text-white">
              GM
            </div>
            <span className="font-semibold tracking-tight">
              Google Maps Optimizer
            </span>
          </div>
          <span className="rounded-full bg-mist px-3 py-1 text-xs font-medium text-slate-600">
            Foundation v1
          </span>
        </header>

        <div className="max-w-2xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-accent">
            Measure · Diagnose · Act
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-ink sm:text-6xl">
            A trustworthy foundation for local visibility decisions.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
            The application shell is ready. Product modules will be added one
            reviewed milestone at a time, starting with the data model and
            authentication boundary.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <Button>Foundation ready</Button>
            <span className="text-sm text-slate-500">
              No product data is connected yet.
            </span>
          </div>
        </div>

        <footer className="text-sm text-slate-400">
          Next.js frontend · FastAPI backend · PostgreSQL · Redis/Celery
        </footer>
      </section>
    </main>
  );
}
