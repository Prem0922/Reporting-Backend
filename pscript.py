import requests
import random
import json
import uuid
from datetime import datetime, timedelta
from database_postgresql import db

# --- API Endpoints (ensure your Flask app is running on localhost:5000) ---
DATABASE_API_URL_TESTS = "http://localhost:5000/api/tests"
DATABASE_API_URL_STRUCTURED_TESTCASES = "http://localhost:5000/api/testcases"
DATABASE_API_URL_REQUIREMENTS = "http://localhost:5000/api/requirements"
DATABASE_API_URL_TEST_RUNS = "http://localhost:5000/api/testruns"
DATABASE_API_URL_DEFECTS = "http://localhost:5000/api/defects"
DATABASE_API_URL_TEST_TYPE_SUMMARY = "http://localhost:5000/api/testtypesummary"
DATABASE_API_URL_TRANSIT_METRICS = "http://localhost:5000/api/transitmetricsdaily"

# --- Lists of possible values for requirements ---
REQUIREMENT_ID_PREFIXES = ["F-FVM", "F-GATE", "F-BUS", "F-ALL", "TC-F-FV", "TC-F-GA", "BU", "NF-GATE", "NF-ALL", "NF-FV"]
TITLES = [
    "Purchase TransitCard using FVM",
    "Reload Card or Add Value",
    "Purchase TransitCard using FVM",
    "FVM should accept Credit and Debit",
    "FVM should accept Cash as payment",
    "Generate Transaction Receipt",
    "Receipt should contain transaction ID, amount",
    "Tap Credit Card with balance on Gate",
    "Gate Reader should be able to tap",
    "Reject Invalid Card on Gate",
    "Identify Entry and Exit on Bus",
    "Send Transaction to Backend",
    "Store offline transactions",
    "Fast transaction completion",
    "High Volume gate processing",
    "Secure stored and transmitted data",
    "Purchase Transit card using FVM",
    "FVM Should timeout after 30 seconds",
    "FVM should retry card processing up",
    "FVM should lock screen when service is not available",
    "FVM Should maintain a transaction History",
    "Gate reader should log every successful otp",
    "Gate reader LED should flash red",
    "Gate reader should display card type",
    "Gate reader should log every rejection",
    "Bus reader should store boarding location",
    "Bus reader should detect direction"
]
DESCRIPTIONS = [
    "User should be able to purchase a smartcard using FVM",
    "User should be able to add value to card",
    "user should be able to reload card",
    "user should be able to purchase a monthly pass",
    "FVM should accept credit and debit cards as payment methods",
    "FVM should accept cash as payment method",
    "FVM should be able to generate a receipt",
    "Receipt should contain transaction ID, amount paid, card id, payment method, date and time",
    "Gate reader should be able to read DesFire,MiFare, credit card and barcode",
    "Bus reader should be able to determine entry vs exit taps",
    "All devices should send transaction immediately to backend server",
    "Gate reader should be able to process minimum of 500k transactions per day without getting stuck",
    "Users should be able to check balance before purchase",
    "FVM should timeout after 30 seconds of inactivity",
    "FVM should lock screen when service mode is active",
    "FVM should show error messages for card read failures",
    "FVM should allow refund option if transaction fails",
    "gate reader should log every successful tap with timestamp",
    "Gate reader should retry backend sync every 30 seconds if offline",
    "Gate reader LED should flash green on success",
    "Gate Reader LED should Flash red on failure",
    "Bus reader should store boarding location on entry",
    "Bus reader should detect direction of tap using GPS Zone"
]
COMPONENTS = ["FVM", "Gate Reader", "Bus Reader", "ALL"]
PRIORITIES = ["Low", "Medium", "High"]
REQUIREMENT_STATUSES = ["Accepted", "Rejected", "In Review", "Design Completed", "Implementation Completed", "Testing Completed", "Done"]
TEST_TYPES = ["Feature", "Regression"]
TEST_STATUSES = ["In review", "Approved", "Draft"]
CREATED_BY_USERS = ["automation_bot", "qa_user1", "qa_user2", "qa_user3"]
TEST_RESULTS = ["Pass", "Fail"]
REMARKS = ["Screen not responsive", "Test Passed Smoothly", "Incorrect result shown", "All Steps Passed", "Minor Delay Observed", "Card Not Detected", "Mechanical Arm Misaligned"]

# --- Lists for Defects ---
DEFECT_TITLES = [
    "NFC Module Not Initializing",
    "Card Tap Not registered",
    "Screen Freeze During Payment",
    "Receipt Not Printed",
    "Wrong Fare Deducted",
    "Timeout during card reload",
    "Gate shows GO on insufficient balance",
    "Incorrect Balance shown after reload",
    "Crash on selecting monthly pass"
]
SEVERITIES = ["Low", "Medium", "High"]
STATUSES = ["Open", "Closed", "In-Progress", "Resolved"]

# --- Lists for Test Type Summary ---
TEST_TYPE_VALUES = ["Stress Test-Bus Readers", "Scalability Test-Backend", "Memory Usage Test - Controller", "Load Test - Gate Readers", "Battery Drain Test - Robot", "Response Time Validation - All Devices", "Performance Test - FVM", "Latency Test - NFC Tap"]
METRICS_VALUES = ["Average Response Time", "CPU Utilization", "Recovery Time From Crash", "Transaction Completion Time", "Concurrent Sessions Handled", "Max Transactions per hour", "Battery Usage per hour", "System Up time", "Memory Usage"]
EXPECTED_FORMATS = ["<=xxxms", "<=xxxms", "<xxxms", ">xxxms", "xx.xx%", ">=xxxx", "<=xx%", ">=xx.xx%", "<=x.xGB"]
ACTUAL_FORMATS_MS = ["xxxms", "xxms"]
ACTUAL_FORMATS_PERCENT = ["xx.xx%"]
ACTUAL_FORMATS_SECONDS = ["x.xs"]
ACTUAL_FORMATS_GB = ["x.xxGB"]
STATUS_VALUES = ["Pass", "Fail"]

# --- Lists for Transit Metrics Daily ---
NOTES_OPTIONS = [
    "All Systems Stable",
    "FVMs under maintenance in Zone B",
    "Normal Operation",
    "Observed High Tap Volume at metro line 3",
    "Minor Delay in gate Readers",
    "Bus Taps Errors Observed",
    "Data Incomplete Due to network Issue",
    "Few gate rejections due to hotlisted cards"
]

# --- Lists for new Structured Test Case columns ---
PRECONDITIONS = [
    "Fare Vending Machine is operational and the Maintainer has a valid login card and PIN.",
    "FVM is operational. An invalid card or incorrect PIN is used.",
    "FVM is operational and patron has valid account-based card and credit/debit method.",
    "FVM is operational. Invalid token/card or authorization failure occurs.",
    "FVM is operational and patron has a valid card.",
    "FVM is online and alarm triggers occur.",
    "FVM components must be operational or fail during test.",
    "Revenue collector must be present with access card.",
    "Maintainer must be logged into the device.",
    "C&C and Monitoring system are connected to FVM.",
    "FVM is on and ready to accept input.",
    "User has a valid smart card.",
    "User taps a non-functional or invalid card.",
    "Simulation environment is configured for stress testing."
]
TEST_STEPS = [
    "1. Verify that the Fare Vending Machine displays the login screen for maintenance mode.\n2. Tap a valid Maintainer card and initiate login.\n3. Enter the correct PIN using the keypad.\n4. Verify that the FVM authenticates the Maintainer login.\n5. Confirm that the MaintenanceManager component creates an event for the login\n6. Verify that the Reporting module sends event data to backend systems.\n7. Verify that the Maintenance screen is displayed to the Maintainer.\n8. Select the option to activate or deactivate a component (e.g., Printer, Card Dispenser).\n9. Confirm that the command is executed and acknowledged by the MaintenanceManager.\n10. Ensure that C&C notifies backend about the component activation/deactivation.\n11. Verify that the event is logged in the system by the Reporting module.",
    "1. Launch the Fare Vending Machine and wait for the login screen.\n2. Tap an unauthorized Maintainer card or enter an invalid PIN.\n3. Verify that the system displays an error message for failed login.\n4. Confirm that the maintenance screen is not shown.\n5. Ensure that an event is logged in the backend indicating invalid login.\n6. Attempting to activate or deactivate a component should be inaccessible.",
    "1. Select preferred language on the Fare Vending Machine.\n2. Choose 'Add Product' option.\n3. Tap the account-based smart card on the reader.\n4. FVM arms the reader and reads the token.\n5. SmartCardProcessor sends token data and requests product catalog.\n6. Catalog is sent back and fare products are displayed.\n7. Select the desired product to purchase.\n8. Choose payment method as Credit/Debit or Mobile Wallet.\n9. Tap the payment card on the reader.\n10. Reader sends token data for authorization and loads product to card.\n11. Confirmation is shown and sales transaction is acknowledged.\n12. Change is issued (if applicable), and receipt is printed.",
    "1. Attempt to add product using an invalid account-based card or payment method.\n2. Proceed through product selection.\n3. Tap card for payment but simulate card rejection or timeout.\n4. Verify that the machine shows an error and cancels transaction.",
    "1. Select language and 'Add Product' on screen.\n2. Tap the smart card on the reader.\n3. Vending POS sends card data to SmartCardProcessor.\n4. Fare products are retrieved and displayed.\n5. Select desired product.\n6. Choose payment method (cash, credit/debit).\n7. Complete payment via respective method.\n8. SmartCardProcessor writes product to card.\n9. Confirmation is displayed and receipt is printed.",
    "1. Simulate a power failure or vibration or key alarm timeout.\n2. Component error screen is displayed .\n3. UI is updated with Service Indicator for staff awareness.\n4. Notification is sent to back-office.",
    "1. Simulate hardware faults like NFCReaderFault, receiptPrinterFault, etc.\n2. MaintenanceManager logs the fault.\n3. Component error screen is displayed.\n4. HMI updates Service Indicator.\n5. Fault is reported to the backend.",
    "1. Select preferred language on the Fare Vending Machine.\n2. Choose 'Add Product' option.\n3. Tap the account-based smart card on the reader.\n4. FVM arms the reader and reads the token.\n5. SmartCardProcessor sends token data and requests product catalog.\n6. Catalog is sent back and fare products are displayed.\n7. Select the desired product to purchase.\n8. Choose payment method as Credit/Debit or Mobile Wallet.\n9. Tap the payment card on the reader.\n10. Reader sends token data for authorization and loads product to card.\n11. Confirmation is shown and sales transaction is acknowledged.\n12. Change is issued (if applicable), and receipt is printed.",
    "1. Select fare product on screen.\n2. Insert coins or bills as shown on the payment screen.\n3. FVM collects and confirms the value.\n4. If user presses cancel before completion, transaction is aborted and cash is returned.\n5. If value is accepted, payment is confirmed and transaction completes.\n6. Receipt is printed, and change is dispensed if applicable."
]
EXPECTED_RESULTS = [
    "Component is activated or deactivated successfully. All actions are logged, and appropriate UI feedback is shown.",
    "Maintainer login fails. Component control options are not shown. No activation/deactivation occurs or is logged.",
    "Product is successfully loaded, transaction is authorized, and receipt is issued.",
    "Transaction fails. Product is not loaded and error message is displayed.",
    "Fare product is written to card and transaction is confirmed.",
    "Alarm is captured, displayed, and reported to backend.",
    "Fault is shown on screen and logged in backend system.",
    "Authorization result displayed within 2 seconds.",
    "Welcome screen should appear within 60 seconds.",
    "Language change should apply in under 1 second."
]

# --- Functions for data generation and sending ---

def generate_dummy_requirement_data():
    """Generates dummy requirement data randomly from predefined lists."""
    prefix = random.choice(REQUIREMENT_ID_PREFIXES)
    random_number = random.randint(100, 999)
    requirement_id = f"{prefix}-{random_number:03d}"  # Ensure 3 digits with leading zeros
    title = random.choice(TITLES)
    description = random.choice(DESCRIPTIONS)
    component = random.choice(COMPONENTS)
    priority = random.choice(PRIORITIES)
    status = random.choice(REQUIREMENT_STATUSES)
    jira_id = f"JIRA-{random.randint(1000, 9999)}"
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Current timestamp

    requirement_data = {
        "requirement_id": requirement_id,
        "title": title,
        "description": description,
        "component": component,
        "priority": priority,
        "status": status,
        "jira_id": jira_id,
        "created_at": created_at
    }
    return requirement_data

def send_requirement_data_to_db(data):
    try:
        success = db.create_requirement(data)
        if success:
            print(f"Successfully created requirement: {data['requirement_id']}")
        else:
            print(f"Failed to create requirement: {data['requirement_id']}")
    except Exception as e:
        print(f"Error creating requirement: {e}")

def fetch_existing_requirement_ids():
    """Fetches existing requirement IDs from the database."""
    try:
        requirements_data = db.get_all_requirements()
        requirement_ids = [req["requirement_id"] for req in requirements_data]
        print(f"Successfully fetched {len(requirement_ids)} requirement IDs.")
        return requirement_ids
    except Exception as e:
        print(f"Error fetching requirement IDs: {e}")
        return []

def generate_structured_test_case(component, requirement_prefix, titles, existing_requirement_ids):
    random_id_part = f"{random.randint(0, 999):03d}"
    random_sub_id_part = f"{random.randint(0, 99):02d}"
    test_case_id = f"TC-F-{component.upper().replace(' ', '-')}-{random_id_part}-{random_sub_id_part}"
    title = random.choice(titles)
    test_type = random.choice(TEST_TYPES)
    status = random.choice(TEST_STATUSES)
    created_by = random.choice(CREATED_BY_USERS)
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Link to an existing requirement ID or generate a dummy one if none exist
    requirement_id = random.choice(existing_requirement_ids) if existing_requirement_ids else f"F-{requirement_prefix}-{random_id_part}"
    
    # New fields: PreCondition, Test_Steps, Expected_Result
    precondition = random.choice(PRECONDITIONS)
    test_steps = random.choice(TEST_STEPS)
    expected_result = random.choice(EXPECTED_RESULTS)
    
    return {
        "test_case_id": test_case_id,
        "title": title,
        "type": test_type,
        "status": status,
        "component": component,
        "requirement_id": requirement_id,
        "created_by": created_by,
        "created_at": created_at,
        "pre_condition": precondition,  # New field
        "test_steps": test_steps,      # New field
        "expected_result": expected_result # New field
    }

def send_structured_test_cases_to_db(data):
    try:
        success_count = db.bulk_create_test_cases(data)
        print(f"Successfully created {success_count} structured test cases.")
    except Exception as e:
        print(f"Error creating structured test cases: {e}")

def generate_test_run_data(test_case_ids):
    """Generates dummy test run data."""
    test_runs = []
    if not test_case_ids:
        print("Warning: No test case IDs available to generate test runs.")
        return test_runs

    for _ in range(20): # Generate 20 dummy test runs
        random_test_case_id = random.choice(test_case_ids)
        # Use UUID instead of hardcoded rid-xxx format to avoid duplicates
        run_id = str(uuid.uuid4())
        execution_date = datetime.now().strftime('%d-%m-%Y %H:%M')
        result = random.choice(TEST_RESULTS)
        observed_time = random.randint(100, 9999)
        executed_by = f"Robot_Unit_0{random.randint(0, 9)}"
        remarks = random.choice(REMARKS)

        test_runs.append({
            "run_id": run_id,
            "test_case_id": random_test_case_id,
            "execution_date": execution_date,
            "result": result,
            "observed_time": observed_time,
            "executed_by": executed_by,
            "remarks": remarks
        })
    return test_runs

def send_test_run_data_to_db(data):
    try:
        success_count = db.bulk_create_test_runs(data)
        print(f"Successfully created {success_count} test runs.")
    except Exception as e:
        print(f"Error creating test runs: {e}")

def generate_dummy_defect_data(test_case_ids):
    """Generates dummy defect data, linking to existing test case IDs."""
    defects = []
    if not test_case_ids:
        print("Warning: No test case IDs available to generate defects.")
        return defects

    for i in range(1, 11):  # Generate 10 dummy defects
        # Use UUID instead of hardcoded RT-xxxxx format to avoid duplicates
        defect_id = str(uuid.uuid4())
        title = random.choice(DEFECT_TITLES)
        severity = random.choice(SEVERITIES)
        status = random.choice(STATUSES)
        test_case_id = random.choice(test_case_ids)
        reported_by_type = random.choice(["qa_user", "Robot_Unit"])
        reported_by_id = f"{random.randint(1, 9):02d}"
        reported_by = f"{reported_by_type}_{reported_by_id}"
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Generate a random fixed_at time later than created_at
        created_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        time_difference = timedelta(days=random.randint(1, 30), hours=random.randint(1, 23), minutes=random.randint(1, 59))
        fixed_at_time = created_time + time_difference
        fixed_at = fixed_at_time.strftime('%Y-%m-%d %H:%M:%S')

        defects.append({
            "defect_id": defect_id,
            "title": title,
            "severity": severity,
            "status": status,
            "test_case_id": test_case_id,
            "reported_by": reported_by,
            "created_at": created_at,
            "fixed_at": fixed_at
        })
    return defects

def send_defect_data_to_db(data):
    try:
        success_count = db.bulk_create_defects(data)
        print(f"Successfully created {success_count} defects.")
    except Exception as e:
        print(f"Error creating defects: {e}")

def generate_dummy_test_type_summary_data():
    """Generates dummy data for the Test Type Summary table."""
    summary_data = []
    for test_type in TEST_TYPE_VALUES:
        metric = random.choice(METRICS_VALUES)
        expected_format = ""
        actual_value = ""
        if "Response Time" in metric or "Completion Time" in metric:
            expected_format = random.choice(["<=xxxms", "<xxxms"])
            actual_value = f"{random.randint(10, 1000)}ms"
        elif "CPU Utilization" in metric or "Battery Usage" in metric:
            expected_format = "<=xx%"
            actual_value = f"{random.uniform(10, 95):.2f}%"
        elif "Recovery Time" in metric:
            expected_format = "<xxxms"
            actual_value = f"{random.uniform(1, 10):.1f}s"
        elif "Concurrent Sessions" in metric or "Max Transactions" in metric:
            expected_format = ">=xxxx"
            actual_value = f"{random.randint(100, 5000)}"
        elif "System Up time" in metric:
            expected_format = ">=xx.xx%"
            actual_value = f"{random.uniform(99.00, 99.99):.2f}%"
        elif "Memory Usage" in metric:
            expected_format = "<=x.xGB"
            actual_value = f"{random.uniform(0.1, 2.5):.2f}GB"

        status = random.choice(STATUS_VALUES)
        test_date = datetime.now() - timedelta(days=random.randint(0, 30))

        summary_data.append({
            "test_type": test_type,
            "metrics": metric,
            "expected": expected_format.replace('xxx', str(random.randint(100, 500))).replace('xx', str(random.randint(1, 99))).replace('x', str(random.randint(1, 5))),
            "actual": actual_value,
            "status": status,
            "test_date": test_date.strftime('%Y-%m-%d')
        })
    return summary_data

def send_test_type_summary_data_to_db(data):
    try:
        success_count = db.bulk_create_test_type_summaries(data)
        print(f"Successfully created {success_count} test type summary entries.")
    except Exception as e:
        print(f"Error creating test type summaries: {e}")

def generate_dummy_transit_metrics_data():
    """Generates dummy data for the Transit Metrics Daily table."""
    today = datetime.now().date()
    metrics_data = []
    for i in range(7):  # Generate data for the last 7 days
        current_date = today - timedelta(days=i)
        fvm_transactions = random.randint(100, 999) if random.random() < 0.5 else random.randint(1000, 9999)
        gate_taps = random.randint(1000, 9999) if random.random() < 0.5 else random.randint(10000, 50000)
        bus_taps = random.randint(1000, 9999)
        success_rate_gate = f"{random.uniform(90.00, 99.99):.2f}"
        success_rate_bus = f"{random.uniform(90.00, 99.99):.2f}"
        avg_response_time = random.randint(50, 500)
        defect_count = random.randint(0, 9)
        notes = random.choice(NOTES_OPTIONS)

        metrics_data.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "fvm_transactions": fvm_transactions,
            "gate_taps": gate_taps,
            "bus_taps": bus_taps,
            "success_rate_gate": success_rate_gate,
            "success_rate_bus": success_rate_bus,
            "avg_response_time": avg_response_time,
            "defect_count": defect_count,
            "notes": notes
        })
    return metrics_data

def send_transit_metrics_data_to_db(data):
    """Sends transit metrics data to the database."""
    try:
        success_count = db.bulk_create_transit_metrics(data)
        print(f"Successfully created {success_count} transit metrics entries.")
    except Exception as e:
        print(f"Error creating transit metrics: {e}")

# --- Main execution block ---
if __name__ == "__main__":
    # Fetch existing requirement IDs before generating structured test cases
    # This ensures that generated test cases can link to actual requirements if they exist.
    existing_requirement_ids = fetch_existing_requirement_ids()

    # --- Generate and send randomly generated requirement data ---
    print("\n--- Sending Randomly Generated Requirement Data ---")
    num_requirements_to_generate = 10
    for _ in range(num_requirements_to_generate):
        requirement_data = generate_dummy_requirement_data()
        print(f"Generated requirement data: {json.dumps(requirement_data, indent=4)}")
        send_requirement_data_to_db(requirement_data)
        print("-" * 30)

    # --- Generate and send structured test case data ---
    print("\n--- Sending Structured Test Case Data ---")
    structured_test_cases_data = []

    # FVM Test Cases
    fvm_titles = [
        "Verify: User should be able to purchase a SmartCard using FVM.",
        "Verify: User should be able to add value to the card.",
        "Verify: User should be able to reload the card.",
        "Verify: User should be able to purchase a monthly pass.",
        "Verify: FVM should accept Credit and Debit cards as payment methods.",
        "Verify: FVM should accept Cash as payment method.",
        "Verify: FVM should be able to generate a receipt.",
        "Verify: Receipt should contain transaction ID, amount paid, card ID, payment method, date and time.",
    ]
    for _ in range(3):
        structured_test_cases_data.append(generate_structured_test_case("FVM", "FVM", fvm_titles, existing_requirement_ids))

    # Gate Reader Test Cases (Functional)
    gate_functional_titles = [
        "Verify: Gate Reader should be able to read DesFire, MiFare, Credit card and Barcode.",
        "Verify: Gate Reader should be able to show the transaction result even if it loses connection with backend server.",
        "Verify: Gate Reader should reject cards with insufficient balance, expired card, hotlisted card, or those tapped multiple times within the passback time limit.",
    ]
    for _ in range(3):
        structured_test_cases_data.append(generate_structured_test_case("GATE READER", "GATE", gate_functional_titles, existing_requirement_ids))

    # Bus Reader Test Cases
    bus_titles = ["Verify: Bus Reader should be able to determine Entry vs Exit taps."]
    for _ in range(2):
        structured_test_cases_data.append(generate_structured_test_case("BUS READER", "BUS", bus_titles, existing_requirement_ids))

    # All Devices Test Cases
    all_titles = [
        "Verify: All devices should send the transaction immediately to backend server.",
        "Verify: All devices should store transactions locally in the event of a communication failure with the backend server.",
    ]
    for _ in range(2):
        structured_test_cases_data.append(generate_structured_test_case("ALL", "ALL", all_titles, existing_requirement_ids))

    # Gate Reader Test Cases (Non-Functional)
    gate_nf_titles = [
        "Verify: Gate Reader should complete the transaction within 500 ms.",
        "Verify: Gate Reader should be able to process minimum of 500k transactions per day without getting stuck.",
    ]
    for _ in range(2):
        # For non-functional test cases, we might want different ID prefixes
        random_id_part = f"{random.randint(0, 999):03d}"
        random_sub_id_part = f"{random.randint(0, 99):02d}"
        test_case_id = f"TC-NF-GATE-{random_id_part}-{random_sub_id_part}"
        # Ensure requirement ID links to an existing one or uses a relevant NF prefix
        requirement_id = random.choice(existing_requirement_ids) if existing_requirement_ids else f"NF-GATE-{random_id_part}"
        
        structured_test_cases_data.append({
            "test_case_id": test_case_id,
            "title": random.choice(gate_nf_titles),
            "type": random.choice(TEST_TYPES), # Can be 'Performance' or 'Scalability'
            "status": random.choice(TEST_STATUSES),
            "component": "GATE READER",
            "requirement_id": requirement_id,
            "created_by": random.choice(CREATED_BY_USERS),
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "pre_condition": random.choice(PRECONDITIONS),
            "test_steps": random.choice(TEST_STEPS),
            "expected_result": random.choice(EXPECTED_RESULTS)
        })

    # FVM Test Cases (Further Functional)
    fv_titles = [
        "Verify: User should be able to check balance before purchase.",
        "Verify: FVM should timeout after 30 seconds of inactivity.",
        "Verify: FVM should support multiple language options.",
        "Verify: FVM should retry card processing up to 3 times on failure.",
        "Verify: FVM should lock screen when service mode is active.",
        "Verify: FVM should show error messages for card read failure.",
        "Verify: FVM should allow refund option if transaction fails.",
        "Verify: FVM should maintain a transaction history for 7 days.",
        "Verify: FVM should sync time with backend every day.",
        "Verify: FVM display brightness should auto-adjust based on lighting.",
    ]
    for _ in range(3):
        structured_test_cases_data.append(generate_structured_test_case("FVM", "FV", fv_titles, existing_requirement_ids))

    # Gate Reader Test Cases (Further Functional)
    ga_titles = [
        "Verify: Gate Reader should log every successful tap with timestamp.",
        "Verify: Gate Reader should retry backend sync every 10 seconds if offline.",
        "Verify: Gate Reader LED should flash green on success.",
        "Verify: Gate Reader LED should flash red on failure.",
        "Verify: Gate Reader should display card type and last 4 digits.",
        "Verify: Gate Reader should support NFC and barcode readers.",
        "Verify: Gate Reader should handle double taps gracefully.",
        "Verify: Gate Reader audio volume should adjust during peak hours.",
        "Verify: Gate Reader should log every rejection reason.",
        "Verify: Gate Reader should operate in temperatures from -10°C to 50°C.",
    ]
    for _ in range(3):
        structured_test_cases_data.append(generate_structured_test_case("Gate Reader", "GA", ga_titles, existing_requirement_ids))

    # Bus Reader Test Case (Specific Title)
    bus_specific_title = ["Verify: Bus Reader should detect direction of tap using GPS zone."]
    for _ in range(1):
        structured_test_cases_data.append(generate_structured_test_case("Bus Reader", "BU", bus_specific_title, existing_requirement_ids))

    # Send all structured test cases to the new endpoint
    send_structured_test_cases_to_db(structured_test_cases_data)
    print("-" * 30)

    # Fetch existing test case IDs for Test Runs and Defects
    # We fetch them AGAIN here to ensure we have the IDs of the newly added structured test cases
    print("\n--- Re-fetching Existing Test Case IDs (including newly added structured ones) ---")
    try:
        fetched_test_cases = db.get_all_test_cases()
        existing_test_case_ids_for_runs_defects = [tc["Test_Case_ID"] for tc in fetched_test_cases]
        print(f"Successfully re-fetched {len(existing_test_case_ids_for_runs_defects)} test case IDs.")
    except Exception as e:
        print(f"Error re-fetching test case IDs: {e}")
        existing_test_case_ids_for_runs_defects = []
    print("-" * 30)

    # --- Generate and send test run data ---
    print("\n--- Sending Test Run Data ---")
    # Use the re-fetched list for test runs and defects
    test_run_data = generate_test_run_data(existing_test_case_ids_for_runs_defects)
    if test_run_data: # Only send if data was generated
        # print(f"Generated test run data: {json.dumps(test_run_data, indent=4)}") # Uncomment to see full test run data
        send_test_run_data_to_db(test_run_data)
    print("-" * 30)

    # --- Generate and send defect data ---
    print("\n--- Sending Defect Data ---")
    defect_data = generate_dummy_defect_data(existing_test_case_ids_for_runs_defects)
    if defect_data: # Only send if data was generated
        # print(f"Generated defect data: {json.dumps(defect_data, indent=4)}") # Uncomment to see full defect data
        send_defect_data_to_db(defect_data)
    print("-" * 30)

    # --- Generate and send Test Type Summary data ---
    print("\n--- Sending Test Type Summary Data ---")
    test_type_summary_data = generate_dummy_test_type_summary_data()
    if test_type_summary_data: # Only send if data was generated
        # print(f"Generated test type summary data: {json.dumps(test_type_summary_data, indent=4)}") # Uncomment to see full summary data
        send_test_type_summary_data_to_db(test_type_summary_data)
    print("-" * 30)

    # --- Generate and send Transit Metrics Daily data ---
    print("\n--- Sending Transit Metrics Daily Data ---")
    transit_metrics_data = generate_dummy_transit_metrics_data()
    if transit_metrics_data: # Only send if data was generated
        # print(f"Generated transit metrics daily data: {json.dumps(transit_metrics_data, indent=4)}") # Uncomment to see full metrics data
        send_transit_metrics_data_to_db(transit_metrics_data)
    print("-" * 30)