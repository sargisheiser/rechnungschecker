# RechnungsChecker Test Workflows

This document describes all test workflows and the corresponding test files.

---

## 1. XRechnung Validation

### Test Files Location: `test_files/xrechnung/`

| File | Expected Result | Description |
|------|-----------------|-------------|
| `valid_xrechnung.xml` | VALID | Complete XRechnung 3.0 with all required fields |
| `invalid_missing_buyer_reference.xml` | INVALID | Missing Leitweg-ID (BuyerReference) |
| `invalid_calculation_error.xml` | INVALID | Tax calculation mismatch (19% of 100 != 20) |
| `invalid_malformed_xml.xml` | ERROR | Malformed XML with unclosed tags |

### Test Steps:
1. Go to Dashboard
2. Upload each XML file
3. Verify validation result matches expected result
4. For invalid files, verify error messages are shown in German
5. Download PDF report for valid invoices

---

## 2. ZUGFeRD Validation

### Test Files Location: `test_files/zugferd/`

| File | Expected Result | Description |
|------|-----------------|-------------|
| `valid_zugferd_en16931.xml` | VALID | Complete ZUGFeRD EN16931 profile |
| `invalid_missing_seller.xml` | INVALID | Missing seller information |
| `invalid_wrong_currency.xml` | INVALID | Invalid currency code (XXX) |

### Test Steps:
1. Go to Dashboard
2. Upload each XML file
3. Verify ZUGFeRD profile is detected correctly
4. Verify validation result matches expected result
5. Check that warnings/errors are displayed properly

---

## 3. PDF Conversion

### Test Files Location: `test_files/pdf_conversion/`

To generate test PDFs, run:
```bash
cd test_files/pdf_conversion
pip install reportlab
python generate_test_pdfs.py
```

Alternatively, open `sample_invoice.html` in a browser and print to PDF.

| File | Expected Result | Description |
|------|-----------------|-------------|
| `valid_invoice.pdf` | SUCCESS | Standard invoice with all data |
| `minimal_invoice.pdf` | SUCCESS with warnings | Minimal data, some fields missing |
| `complex_invoice.pdf` | SUCCESS | Multi-line item complex invoice |
| `not_an_invoice.pdf` | FAIL or poor extraction | Not an invoice document |

### Test Steps:
1. Go to /konvertierung
2. Upload PDF file
3. Verify data extraction in preview step
4. Check confidence indicator
5. Test editing extracted fields
6. Select output format (XRechnung or ZUGFeRD)
7. Convert and download result
8. Validate the downloaded file

---

## 4. Guest Validation (Rate Limiting)

### Test Steps:
1. Open browser in incognito/private mode
2. Go to landing page
3. Upload a valid XML file
4. Verify "3 free validations" counter
5. Upload 3 more files
6. Verify limit message appears after 3 validations
7. Clear cookies and verify counter resets

---

## 5. User Authentication Flow

### Test Steps:

#### Registration:
1. Go to /registrieren
2. Register with new email
3. Check console for verification code (dev mode)
4. Enter code on verification page
5. Verify redirect to dashboard

#### Login:
1. Go to /login
2. Enter credentials
3. Verify redirect to dashboard

#### Password Reset:
1. Go to /login
2. Click "Passwort vergessen?"
3. Enter email
4. Check console for reset link (dev mode)
5. Click link or copy URL
6. Enter new password
7. Verify login works with new password

---

## 6. Subscription & Billing

### Test Steps:
1. Login as free user
2. Go to /preise
3. Select a plan (Starter, Pro, or Steuerberater)
4. Complete demo checkout (uses test mode)
5. Verify plan change on dashboard
6. Test plan limits:
   - Free: 10 validations/month
   - Starter: 100 validations/month
   - Pro: Unlimited validations
7. Test "Abo verwalten" button

---

## 7. API Keys (Pro/Steuerberater only)

### Test Steps:
1. Login as Pro or Steuerberater user
2. Go to /api-keys
3. Create new API key
4. Copy the key (only shown once!)
5. Test API with curl:
```bash
curl -X POST http://localhost:8000/api/v1/validate/ \
  -H "X-API-Key: your_api_key_here" \
  -F "file=@test_files/xrechnung/valid_xrechnung.xml"
```
6. Verify usage counter increases
7. Test deactivating key
8. Test deleting key

---

## 8. Client Management (Steuerberater only)

### Test Steps:
1. Login as Steuerberater user
2. Go to /mandanten
3. Create new client
4. Verify client appears in list
5. Edit client details
6. Go to Dashboard
7. Select client from dropdown
8. Upload and validate file (should be associated with client)
9. Verify validation count for client increases
10. Deactivate client
11. Delete client

---

## 9. Validation History

### Test Steps:
1. Login and perform several validations
2. Go to Dashboard
3. Verify recent validations shown
4. Click "Alle anzeigen" for full history
5. Click on a validation to see details
6. Add/edit notes on validation detail page
7. Download PDF report

---

## 10. Batch Upload (Starter+)

### Test Steps:
1. Login as Starter, Pro, or Steuerberater user
2. Go to Dashboard
3. Select multiple XML files (up to 10)
4. Upload batch
5. Verify all files processed
6. Check results for each file

---

## 11. Edge Cases

### Empty File:
- Create empty .xml file
- Upload and verify error message

### Large File:
- Create XML > 10MB
- Upload and verify file size error

### Wrong File Type:
- Upload .txt, .doc, .jpg files
- Verify file type error

### Special Characters:
- Test files with German umlauts in filename
- Test invoice data with special characters

---

## Quick Test Checklist

- [ ] XRechnung valid file validates correctly
- [ ] XRechnung invalid file shows errors
- [ ] ZUGFeRD valid file validates correctly
- [ ] ZUGFeRD invalid file shows errors
- [ ] PDF conversion extracts data correctly
- [ ] Guest validation limit works (3 free)
- [ ] Registration sends verification email
- [ ] Password reset sends email
- [ ] Login/logout works
- [ ] Plan upgrade works
- [ ] API key authentication works
- [ ] Client management works (Steuerberater)
- [ ] Validation history shows correctly
- [ ] PDF report downloads correctly
- [ ] Error messages display in German

---

## Notes

- In development mode, emails are printed to the backend console
- Stripe is in test/demo mode - no real charges
- OCR for scanned PDFs requires Tesseract installation
- All validation uses the KoSIT validator
