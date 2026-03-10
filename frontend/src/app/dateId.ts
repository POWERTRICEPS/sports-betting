export const APP_TIME_ZONE = "America/Los_Angeles";

type DateParts = {
  year: number;
  month: number;
  day: number;
};

export function getDatePartsInTimeZone(
  date: Date,
  timeZone: string = APP_TIME_ZONE,
): DateParts {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);

  const year = Number(parts.find((p) => p.type === "year")?.value);
  const month = Number(parts.find((p) => p.type === "month")?.value);
  const day = Number(parts.find((p) => p.type === "day")?.value);

  return { year, month, day };
}

export function dateIdFromParts({ year, month, day }: DateParts): string {
  return [
    String(year),
    String(month).padStart(2, "0"),
    String(day).padStart(2, "0"),
  ].join("");
}

export function getTodayDateId(timeZone: string = APP_TIME_ZONE): string {
  return dateIdFromParts(getDatePartsInTimeZone(new Date(), timeZone));
}

export function getTodayDateInTimeZone(
  timeZone: string = APP_TIME_ZONE,
): Date {
  const { year, month, day } = getDatePartsInTimeZone(new Date(), timeZone);
  return new Date(year, month - 1, day);
}
