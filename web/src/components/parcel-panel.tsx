"use client";

import { ExternalLink, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { fmtAcres, fmtDate, fmtSqft } from "@/lib/format";
import { groupFor } from "@/lib/map-style";
import type { Meta, ParcelDetail, Theme } from "@/lib/types";

interface Props {
  meta: Meta;
  theme: Theme;
  detail: ParcelDetail | null | undefined; // undefined = still loading, null = not found
  preferredAddress: string | null; // the address the user searched for, if any
  onClose: () => void;
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[8.5rem_1fr] gap-x-3 py-1.5 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-foreground">{children}</dd>
    </div>
  );
}

const Missing = () => <span className="text-muted-foreground">Not in City GIS</span>;

function coded(code: string | null, labels: Record<string, string>) {
  if (!code) return <Missing />;
  return (
    <>
      {labels[code] ?? code} <span className="text-muted-foreground">({code})</span>
    </>
  );
}

export default function ParcelPanel({ meta, theme, detail, preferredAddress, onClose }: Props) {
  const parcelsSource = meta.sources.find((s) => s.id === "city_land_parcels")!;
  const zoningSource = meta.sources.find((s) => s.id === "city_zoning")!;

  return (
    <aside
      aria-label="Parcel details"
      className="pointer-events-auto absolute inset-x-0 bottom-0 z-20 flex max-h-[58vh] flex-col overflow-hidden rounded-t-xl border bg-background shadow-xl md:inset-x-auto md:top-3 md:right-3 md:bottom-3 md:max-h-none md:w-[400px] md:rounded-xl"
    >
      <div className="flex items-start justify-between gap-3 border-b px-5 pt-4 pb-3">
        <div className="min-w-0">
          {detail === undefined ? (
            <Skeleton className="h-6 w-56" />
          ) : (
            <h2 className="truncate text-base font-semibold tracking-tight">
              {preferredAddress ?? detail?.addresses[0] ?? "No site address on file"}
            </h2>
          )}
          <p className="mt-0.5 font-mono text-xs text-muted-foreground tabular-nums">
            {detail ? (detail.is_assessor_apn ? `APN ${detail.apn}` : `City ID ${detail.apn}`) : " "}
          </p>
        </div>
        <Button variant="ghost" size="icon" className="-mr-2 shrink-0" onClick={onClose} aria-label="Close parcel details">
          <X />
        </Button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
        {detail === undefined && (
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-3/5" />
          </div>
        )}

        {detail === null && (
          <p className="text-sm text-muted-foreground">
            No details were found for this parcel in the current data release.
          </p>
        )}

        {detail && (
          <>
            <div className="mb-3 flex flex-wrap gap-1.5">
              {detail.zoning && (
                <Badge variant="outline" className="gap-1.5 font-normal">
                  <span
                    aria-hidden
                    className="size-2.5 rounded-[3px] border border-foreground/15"
                    style={{ background: groupFor(meta.lookups.zoning[detail.zoning]?.family ?? "none").color[theme] }}
                  />
                  {detail.zoning}
                </Badge>
              )}
              {detail.specific_plan && (
                <Badge variant="secondary" className="font-normal">
                  {meta.lookups.specific_plan[detail.specific_plan] ?? detail.specific_plan}
                </Badge>
              )}
              {detail.historic && (
                <Badge variant="secondary" className="font-normal">
                  {meta.lookups.historic[detail.historic] ?? detail.historic}
                </Badge>
              )}
            </div>

            {!detail.is_assessor_apn && (
              <p className="mb-3 rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                This is a condominium common area. The City labels it with its own ID, not a County Assessor
                parcel number, so it can&apos;t be matched to County or State records.
              </p>
            )}

            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Zoning &amp; land use</h3>
            <dl className="mt-1">
              <Row label="Zoning">
                {detail.zoning ? (
                  <>
                    {meta.lookups.zoning[detail.zoning]?.label ?? detail.zoning}
                    <div className="text-xs text-muted-foreground">
                      {meta.families.find((f) => f.code === meta.lookups.zoning[detail.zoning!]?.family)?.label}
                    </div>
                  </>
                ) : (
                  <Missing />
                )}
              </Row>
              <Row label="General Plan">{coded(detail.general_plan, meta.lookups.general_plan)}</Row>
              <Row label="Plan area">
                {detail.specific_plan ? (
                  meta.lookups.specific_plan[detail.specific_plan]
                ) : (
                  <span className="text-muted-foreground">None</span>
                )}
              </Row>
              <Row label="Historic status">
                {detail.historic ? (
                  meta.lookups.historic[detail.historic]
                ) : (
                  <span className="text-muted-foreground">None recorded</span>
                )}
              </Row>
              <Row label="Flood note">
                {detail.flood ? (
                  meta.lookups.flood[detail.flood]
                ) : (
                  <span className="text-muted-foreground">None recorded</span>
                )}
              </Row>
            </dl>

            <Separator className="my-3" />

            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Parcel</h3>
            <dl className="mt-1">
              <Row label="Lot area">
                {detail.lot_area_acres != null && detail.lot_area_sqft != null ? (
                  <span className="tabular-nums">
                    {fmtAcres(detail.lot_area_acres)}
                    <span className="text-muted-foreground"> · {fmtSqft(detail.lot_area_sqft)}</span>
                  </span>
                ) : (
                  <Missing />
                )}
              </Row>
              <Row label="Year built">
                {detail.year_built ? <span className="tabular-nums">{detail.year_built}</span> : <Missing />}
              </Row>
              <Row label="Parcel type">{coded(detail.parcel_type, meta.lookups.parcel_type)}</Row>
              <Row label="ZIP / district">
                {detail.zip ?? "—"} · {detail.council_district ?? "—"}
              </Row>
              {detail.address_count > 0 && (
                <Row label={detail.address_count === 1 ? "Address" : `Addresses (${detail.address_count})`}>
                  <ul className="space-y-0.5">
                    {detail.addresses.map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                    {detail.address_count > detail.addresses.length && (
                      <li className="text-muted-foreground">
                        and {detail.address_count - detail.addresses.length} more
                      </li>
                    )}
                  </ul>
                </Row>
              )}
            </dl>
            {detail.n_parts > 1 && (
              <p className="mt-1 text-xs text-muted-foreground">
                Stored as {detail.n_parts} separate shapes in City GIS; merged here into one parcel.
              </p>
            )}

            <Separator className="my-3" />

            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Sources</h3>
            <ul className="mt-2 space-y-2 text-sm">
              <li>
                <a
                  className="inline-flex items-center gap-1 text-link underline-offset-2 hover:underline"
                  href={`${parcelsSource.url}/query?where=OBJECTID+IN+(${detail.object_ids.join(",")})&outFields=*&f=html`}
                  target="_blank"
                  rel="noreferrer"
                >
                  This parcel&apos;s City GIS record <ExternalLink className="size-3" />
                </a>
                <div className="text-xs text-muted-foreground">
                  {parcelsSource.attribution} · retrieved {fmtDate(parcelsSource.retrieved_at)}; flood note from the
                  Zoning layer, retrieved {fmtDate(zoningSource.retrieved_at)}
                </div>
              </li>
              <li>
                <a
                  className="inline-flex items-center gap-1 text-link underline-offset-2 hover:underline"
                  href={meta.links.zoning_code_home}
                  target="_blank"
                  rel="noreferrer"
                >
                  {meta.links.zoning_code_label} <ExternalLink className="size-3" />
                </a>
              </li>
              <li>
                <a
                  className="inline-flex items-center gap-1 text-link underline-offset-2 hover:underline"
                  href={meta.links.general_plan_home}
                  target="_blank"
                  rel="noreferrer"
                >
                  {meta.links.general_plan_label} <ExternalLink className="size-3" />
                </a>
              </li>
            </ul>
          </>
        )}
      </div>

      <p className="border-t px-5 py-2.5 text-[11px] leading-snug text-muted-foreground">
        Screening tool only: not a zoning determination, legal advice, or an appraisal. Year built is as recorded in
        City GIS.
      </p>
    </aside>
  );
}
