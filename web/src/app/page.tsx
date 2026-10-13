import AppShell from "@/components/app-shell";
import type { Meta } from "@/lib/types";

// meta.json is written by the pipeline (`uv run pipeline export`) and read at
// build time, so headline counts and source dates are in the first HTML.
import metaJson from "../../public/data/meta.json";

const meta = metaJson as unknown as Meta;

export default function Home() {
  return <AppShell meta={meta} />;
}
