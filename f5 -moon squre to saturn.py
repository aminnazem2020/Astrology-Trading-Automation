import swisseph as swe
import datetime
import csv
import os

# -------- CONFIGURATION --------
EPHE_PATH = r"d:\amin\1404\AsTrading"  # folder containing ephemeris files
OUTPUT_CSV = os.path.join(EPHE_PATH, "moon_saturn_squares.csv")
START_DATE = datetime.datetime(2025, 1, 1)
END_DATE = datetime.datetime(2025, 12, 31)
STEP_HOURS = 1
TOLERANCE_DEG = 0.5
REFINE_MINUTES = 1
# -------------------------------

swe.set_ephe_path(EPHE_PATH)

def moon_saturn_angle(jd):
    moon_res = swe.calc_ut(jd, swe.MOON)
    saturn_res = swe.calc_ut(jd, swe.SATURN)
    moon_long = moon_res[0][0]
    saturn_long = saturn_res[0][0]
    return (moon_long - saturn_long + 360) % 360

def square_distance(angle):
    return min(abs(angle - 90), abs(angle - 270))

def refine_square(base_dt, lower_dt, upper_dt, target_deg=90.0):
    def dist(dt):
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
        angle = moon_saturn_angle(jd)
        return square_distance(angle), angle

    left = lower_dt
    right = upper_dt
    best = base_dt
    best_dist, best_angle = dist(base_dt)

    while (right - left) > datetime.timedelta(minutes=REFINE_MINUTES):
        mid = left + (right - left) / 2
        mid = datetime.datetime(mid.year, mid.month, mid.day, mid.hour, int(mid.minute))
        d_mid, angle_mid = dist(mid)
        if d_mid < best_dist:
            best = mid
            best_dist = d_mid
            best_angle = angle_mid
        d_left, _ = dist(left)
        d_right, _ = dist(right)
        if d_left < d_right:
            right = mid
        else:
            left = mid

    return best, best_angle, best_dist

def scan_squares(start, end):
    results = []
    current = start

    while current <= end:
        jd = swe.julday(current.year, current.month, current.day, current.hour + current.minute / 60.0)
        angle = moon_saturn_angle(jd)
        dist_to_square = square_distance(angle)

        if dist_to_square <= TOLERANCE_DEG:
            lower = current - datetime.timedelta(hours=STEP_HOURS)
            upper = current + datetime.timedelta(hours=STEP_HOURS)
            base = current
            refined_dt, refined_angle, refined_dist = refine_square(base, lower, upper)

            if results and abs((refined_dt - results[-1]["datetime"]).total_seconds()) < 3600:
                pass  # skip near-duplicate
            else:
                results.append({
                    "datetime": refined_dt,
                    "moon_longitude": None,
                    "moon_latitude": None,
                    "saturn_longitude": None,
                    "saturn_latitude": None,
                    "angular_difference": refined_angle,
                    "distance_from_exact_square": refined_dist
                })

        current += datetime.timedelta(hours=STEP_HOURS)

    # Now fill in longitude/latitude details
    for entry in results:
        dt = entry["datetime"]
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
        moon_res = swe.calc_ut(jd, swe.MOON)
        saturn_res = swe.calc_ut(jd, swe.SATURN)

        entry["moon_longitude"] = moon_res[0][0]
        entry["moon_latitude"] = moon_res[0][1]
        entry["saturn_longitude"] = saturn_res[0][0]
        entry["saturn_latitude"] = saturn_res[0][1]
        entry["angular_difference"] = abs((entry["moon_longitude"] - entry["saturn_longitude"] + 360) % 360)

    return results

def save_to_csv(results, filename):
    path = os.path.abspath(filename)
    with open(filename, "w", newline="") as csvfile:
        fieldnames = [
            "datetime_iso",
            "moon_longitude",
            "moon_latitude",
            "saturn_longitude",
            "saturn_latitude",
            "angular_difference",
            "distance_from_exact_square"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "datetime_iso": r["datetime"].isoformat(sep=" "),
                "moon_longitude": f"{r['moon_longitude']:.6f}",
                "moon_latitude": f"{r['moon_latitude']:.6f}",
                "saturn_longitude": f"{r['saturn_longitude']:.6f}",
                "saturn_latitude": f"{r['saturn_latitude']:.6f}",
                "angular_difference": f"{r['angular_difference']:.6f}",
                "distance_from_exact_square": f"{r['distance_from_exact_square']:.6f}"
            })
    print(f"✅ Saved {len(results)} square event(s) to: {path}")

def main():
    results = scan_squares(START_DATE, END_DATE)
    save_to_csv(results, OUTPUT_CSV)

if __name__ == "__main__":
    main()
