"""
PII Redaction Evaluation Engine
Computes Precision, Recall, F1-Score, and Accuracy metrics across entity types
using ground-truth annotated benchmark passages from the document.
"""

from redact import setup_engines, ALLOW_LIST
import json

def run_evaluation():
    analyzer, anonymizer, operators, threshold = setup_engines(score_threshold=0.4)
    entities = list(operators.keys())

    # Ground Truth Test Suite containing representative passages with annotated PII entities
    test_dataset = [
        {
            "text": "Contact Lead Manager Rashi Patil at rashhi.patil@gmail.com or call +91 9876543210.",
            "ground_truth": [
                {"entity": "PERSON", "text": "Rashi Patil"},
                {"entity": "EMAIL_ADDRESS", "text": "rashhi.patil@gmail.com"},
                {"entity": "PHONE_NUMBER", "text": "+91 9876543210"}
            ]
        },
        {
            "text": "Auditor Rohan Dey (rohan.dey@gmail.com) registered at 192.168.1.45 on 15/08/1990.",
            "ground_truth": [
                {"entity": "PERSON", "text": "Rohan Dey"},
                {"entity": "EMAIL_ADDRESS", "text": "rohan.dey@gmail.com"},
                {"entity": "IP_ADDRESS", "text": "192.168.1.45"},
                {"entity": "DATE_TIME", "text": "15/08/1990"}
            ]
        },
        {
            "text": "Company Infosys Limited has CIN L72200KA1981PLC004265 and PAN ABCDE1234F.",
            "ground_truth": [
                {"entity": "ORGANIZATION", "text": "Infosys Limited"},
                {"entity": "US_SSN", "text": "ABCDE1234F"}
            ]
        },
        {
            "text": "Director John Doe, SSN 000-12-3456, paid via Credit Card 4532015698741234.",
            "ground_truth": [
                {"entity": "PERSON", "text": "John Doe"},
                {"entity": "US_SSN", "text": "000-12-3456"},
                {"entity": "CREDIT_CARD", "text": "4532015698741234"}
            ]
        },
        {
            "text": "REGISTERED OFFICE: 45 MG Road, Bangalore 560001, Karnataka.",
            "ground_truth": [
                {"entity": "LOCATION", "text": "45 MG Road, Bangalore 560001, Karnataka"}
            ]
        },
        {
            "text": "E-MAIL AND TELEPHONE: Email: cs.connect@scaler.com Telephone: +91 20 45053237",
            "ground_truth": [
                {"entity": "EMAIL_ADDRESS", "text": "cs.connect@scaler.com"},
                {"entity": "PHONE_NUMBER", "text": "+91 20 45053237"}
            ]
        },
        {
            "text": "Section P856, Ticket #98765 and Clause A1 are non-sensitive internal reference tokens.",
            "ground_truth": [] # Negative test cases to measure Precision & TN
        },
        {
            "text": "For queries, email support@scaler.com or visit 10.0.0.1 on 2024-05-20.",
            "ground_truth": [
                {"entity": "EMAIL_ADDRESS", "text": "support@scaler.com"},
                {"entity": "IP_ADDRESS", "text": "10.0.0.1"},
                {"entity": "DATE_TIME", "text": "2024-05-20"}
            ]
        },
        {
            "text": "Aadhaar number of Promoter is 2345 6789 0123. DOB: 01/01/1985.",
            "ground_truth": [
                {"entity": "US_SSN", "text": "2345 6789 0123"},
                {"entity": "DATE_TIME", "text": "01/01/1985"}
            ]
        },
        {
            "text": "Registrar Link Intime India Pvt Ltd operates from Mumbai, Maharashtra.",
            "ground_truth": [
                {"entity": "ORGANIZATION", "text": "Link Intime India Pvt Ltd"},
                {"entity": "LOCATION", "text": "Mumbai"},
                {"entity": "LOCATION", "text": "Maharashtra"}
            ]
        },
        {
            "text": "Order #40094400 and Application No 141032 processed successfully.",
            "ground_truth": [] # Negative test cases (order numbers shouldn't be redacted as SSN)
        }
    ]

    metrics = {e: {"TP": 0, "FP": 0, "FN": 0, "TN": 0} for e in entities}

    for sample in test_dataset:
        text = sample["text"]
        gt_list = sample["ground_truth"]
        results = analyzer.analyze(
            text=text,
            entities=entities,
            language='en',
            score_threshold=threshold,
            allow_list=ALLOW_LIST
        )

        detected_entities = [{"entity": r.entity_type, "text": text[r.start:r.end]} for r in results]

        # Match detected vs ground truth
        gt_matched = [False] * len(gt_list)
        det_matched = [False] * len(detected_entities)

        for i, gt in enumerate(gt_list):
            for j, det in enumerate(detected_entities):
                if not det_matched[j] and (gt["text"] in det["text"] or det["text"] in gt["text"]):
                    metrics[gt["entity"]]["TP"] += 1
                    gt_matched[i] = True
                    det_matched[j] = True
                    break

        for i, matched in enumerate(gt_matched):
            if not matched:
                metrics[gt_list[i]["entity"]]["FN"] += 1

        for j, matched in enumerate(det_matched):
            if not matched:
                entity_type = detected_entities[j]["entity"]
                if entity_type in metrics:
                    metrics[entity_type]["FP"] += 1

        if not gt_list and not detected_entities:
            for e in entities:
                metrics[e]["TN"] += 1

    overall_tp = sum(m["TP"] for m in metrics.values())
    overall_fp = sum(m["FP"] for m in metrics.values())
    overall_fn = sum(m["FN"] for m in metrics.values())
    overall_tn = sum(m["TN"] for m in metrics.values())

    precision = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0
    recall = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (overall_tp + overall_tn) / (overall_tp + overall_tn + overall_fp + overall_fn) if (overall_tp + overall_tn + overall_fp + overall_fn) > 0 else 0

    print("==================================================")
    print("         PII REDACTION EVALUATION REPORT         ")
    print("==================================================")
    print(f"Overall Accuracy : {accuracy * 100:.2f}%")
    print(f"Overall Precision: {precision * 100:.2f}%")
    print(f"Overall Recall   : {recall * 100:.2f}%")
    print(f"Overall F1-Score : {f1_score * 100:.2f}%")
    print("--------------------------------------------------")

    print("\nPer-Entity Performance Breakdown:")
    report_rows = []
    for ent, m in metrics.items():
        tp, fp, fn, tn = m["TP"], m["FP"], m["FN"], m["TN"]
        p = tp / (tp + fp) if (tp + fp) > 0 else 1.0 if fn == 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 1.0 if fp == 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 1.0
        
        print(f"{ent:15s} | TP:{tp:2d} | FP:{fp:2d} | FN:{fn:2d} | Precision:{p*100:6.1f}% | Recall:{r*100:6.1f}% | F1:{f1*100:6.1f}%")
        report_rows.append({
            "entity": ent,
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(p * 100, 2),
            "recall": round(r * 100, 2),
            "f1": round(f1 * 100, 2),
            "accuracy": round(acc * 100, 2)
        })

    return {
        "overall_precision": round(precision * 100, 2),
        "overall_recall": round(recall * 100, 2),
        "overall_f1": round(f1_score * 100, 2),
        "overall_accuracy": round(accuracy * 100, 2),
        "per_entity": report_rows
    }

if __name__ == "__main__":
    run_evaluation()
