import time
from app import redact_text   # imports your redact_text() function

# --- Sample test cases (text and ground truth labels) ---
test_cases = [
    {
        "text": "Patient Abrar Hussain from RV University, Bangalore, phone 9876543210, email abrar@rv.edu.in.",
        "expected_labels": ["NAME", "LOCATION", "PHONE", "EMAIL"]
    },
    {
        "text": "Contact Dr. R. Singh (SSN 123-45-6789) at 12/03/2024 for follow-up.",
        "expected_labels": ["NAME", "SSN", "DATE"]
    },
    {
        "text": "Address: 45 MG Road, Chennai 600001. IP: 192.168.1.1",
        "expected_labels": ["ADDRESS_SIMPLE", "IP"]
    }
]

# --- Metrics ---
total_expected = 0
total_detected = 0
total_correct = 0
processing_times = []

# --- Run tests ---
for case in test_cases:
    text = case["text"]
    expected = set(case["expected_labels"])
    total_expected += len(expected)

    start = time.time()
    redacted_text, detections = redact_text(text)
    end = time.time()
    processing_times.append(end - start)

    detected_labels = set([d["label"] for d in detections])
    total_detected += len(detected_labels)
    total_correct += len(detected_labels & expected)

    print("\nInput:", text)
    print("Detected:", detected_labels)
    print("Expected:", expected)
    print("Redacted Output:", redacted_text)
    print("Time:", round(end - start, 4), "seconds")

# --- Compute metrics ---
accuracy = total_correct / total_expected if total_expected else 0
avg_time = sum(processing_times) / len(processing_times)

print("\n--- Evaluation Summary ---")
print(f"Detection Accuracy: {accuracy*100:.1f}%")
print(f"Average Processing Time: {avg_time:.4f} seconds per text")

# --- HIPAA checklist summary (manual but shown programmatically) ---
covered_identifiers = [
    "NAME", "EMAIL", "PHONE", "SSN", "ADDRESS_SIMPLE", "DATE",
    "MRN", "CREDIT_CARD", "IP"
]
print("\nHIPAA Alignment Check:")
print(f"Identifiers covered: {len(covered_identifiers)} / 18 (basic textual identifiers)")
print("Covers: names, contacts, dates, addresses, IDs, financial info, digital identifiers.")
print("Not covered: photos, fingerprints, full-face images, biometric data, device IDs, etc.")
