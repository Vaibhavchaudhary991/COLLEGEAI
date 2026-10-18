"""
Management command: load_sample_documents

Populates realistic college documents (Academic regulations, Placements,
Hostel/Campus rules, Scholarships, and Library facilities) and indexes them
into ChromaDB so the RAG assistant is immediately operational.

Usage:
  python manage.py load_sample_documents
  python manage.py load_sample_documents --reindex
"""

import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.conf import settings
from documents.models import DocumentCategory, Document
from documents.services.document_service import process_document

SAMPLE_DOCS = [
    {
        "category": "Academics",
        "category_desc": "Academic curriculum, grading rules, attendance, and exam guidelines",
        "title": "Academic Regulations and Examination Guidelines",
        "filename": "Academic_Regulations_and_Examination_Guidelines.txt",
        "description": "Rules regarding attendance, internal assessments, end-semester exams, grading scale, and detention policy.",
        "content": """ACADEMIC REGULATIONS AND EXAMINATION GUIDELINES
COLLEGE OF ENGINEERING & TECHNOLOGY

1. ATTENDANCE REQUIREMENTS
- Minimum Mandatory Attendance: Students must maintain at least 75% attendance in every course (theory, practicals, tutorials) to be eligible to appear for the End-Semester Examination.
- Medical Condonation: If attendance falls between 65% and 74%, condonation may be granted by the Dean of Academic Affairs upon submission of verified medical documents within 7 working days of absence.
- Detention Policy: Students with attendance below 65% in any course will be detained ('FA' - Failure due to Attendance) in that specific course and must re-register when the course is offered next.

2. EVALUATION & EXAMINATION SCHEME
- Continuous Internal Assessment (CIA): 40% weightage
  * Mid-Term Examination 1: 15%
  * Mid-Term Examination 2: 15%
  * Quizzes, Assignments, and Class Participation: 10%
- End Semester Examination (ESE): 60% weightage
- Passing Criteria: A minimum of 40% aggregate marks (CIA + ESE) and at least 35% marks in the End-Semester Examination is required to pass a course.

3. GRADING SCALE (10-Point Scale)
- O  (Outstanding): 90% - 100%  -> Grade Point 10
- A+ (Excellent):   80% - 89%   -> Grade Point 9
- A  (Very Good):   70% - 79%   -> Grade Point 8
- B+ (Good):        60% - 69%   -> Grade Point 7
- B  (Above Avg):   55% - 59%   -> Grade Point 6
- C  (Average):     50% - 54%   -> Grade Point 5
- P  (Pass):        40% - 49%   -> Grade Point 4
- F  (Fail):        Below 40%   -> Grade Point 0

4. RE-EVALUATION & RE-CHECKING
- Students dissatisfied with their evaluation can apply for re-evaluation within 15 days of official result declaration.
- Re-evaluation fee: Rs. 500 per subject via the Student ERP Portal.
- Supplementary / Backlog examinations are conducted twice a year: July (Summer session) and January (Winter session).

5. KEY ACADEMIC DATES (ACADEMIC YEAR 2026-2027)
- Autumn Semester Commences: August 1, 2026
- Mid-Term Examinations: October 10 to October 18, 2026
- Last Day of Instruction: November 25, 2026
- End-Semester Examinations: December 1 to December 20, 2026
- Winter Vacation: December 21, 2026 to January 10, 2027
- Spring Semester Registration: January 11, 2027
"""
    },
    {
        "category": "Placements",
        "category_desc": "Campus placement drives, internships, training, and company policies",
        "title": "Training, Internship, and Placement Policy",
        "filename": "Training_Internship_and_Placement_Policy.txt",
        "description": "Rules for campus placements, CGPA eligibility criteria, Dream and Super-Dream company categories, and internship NOC procedures.",
        "content": """CAMPUS TRAINING AND PLACEMENT CELL POLICY
DIRECTORATE OF CORPORATE RELATIONS & PLACEMENTS

1. ELIGIBILITY CRITERIA FOR CAMPUS RECRUITMENT
- Minimum CGPA Requirement: A minimum cumulative GPA of 6.50 with no active backlogs across previous semesters is required for registration with the Placement Cell.
- 10th & 12th Cutoffs: Many tier-1 hiring companies mandate at least 60% or 65% aggregate marks in 10th and 12th standard board exams.
- Attendance at Training Sessions: 85% attendance is mandatory in soft-skills, aptitude training, and technical mock interview workshops conducted by the T&P Cell.

2. OFFER TIERS & ONE-STUDENT-ONE-OFFER POLICY
- Tier 1 (Core / Standard): CTC up to 6.5 LPA
- Tier 2 (Dream Category): CTC between 6.5 LPA and 12 LPA
- Tier 3 (Super Dream): CTC exceeding 12 LPA
- Rule: Once a student receives an offer in Tier 1, they are only eligible to apply for Tier 2 or Tier 3 companies. Once a student gets a Dream Offer (Tier 2), they can only sit for Super Dream companies. Once a Super Dream offer is secured, the student is officially placed and exit the drive.

3. SUMMER INTERNSHIPS & NOC PROCEDURE
- Pre-final year students (6th semester) must complete a mandatory 6 to 8-week summer internship.
- To obtain a No Objection Certificate (NOC) for off-campus internships:
  1. Submit the company offer letter along with job role and mentor details on the ERP portal.
  2. Obtain signature from the Head of Department (HOD).
  3. Final approval and NOC issued by the Placement Officer within 3 working days.

4. DRESS CODE & CODE OF CONDUCT
- Mandatory Formals: Men must wear a formal plain light shirt, dark trousers, tie, and polished leather shoes. Women must wear formal western business attire or formal Indian salwar suit.
- Blacklisting: If a student registers for a company drive, clears the shortlist, and fails to attend the test or interview without prior medical notice, they will be barred from the next 3 campus recruitment drives.

5. PLACEMENT CELL CONTACT DETAILS
- Office Location: Room 204, Administrative Block, 2nd Floor
- Email: placements@college.edu / tnpoffice@college.edu
- Helpline Phone: +91-11-2345-6789 (Ext: 204)
- Working Hours: Monday to Friday, 9:00 AM - 5:30 PM
- Head of Placements: Dr. A. Sharma
"""
    },
    {
        "category": "Campus & Hostel",
        "category_desc": "Hostel accommodations, gate timings, dining mess, sports, and campus safety",
        "title": "Hostel Regulations and Campus Facilities Handbook",
        "filename": "Hostel_Regulations_and_Campus_Facilities_Handbook.txt",
        "description": "Hostel gate timings, mess schedule, health centre, ambulance contact, Wi-Fi credentials, and anti-ragging measures.",
        "content": """HOSTEL REGULATIONS AND CAMPUS LIFE HANDBOOK
OFFICE OF THE CHIEF WARDEN & STUDENT WELFARE

1. HOSTEL GATE TIMINGS & CURFEW
- Weekday In-Time: 9:30 PM strictly for all hostel residents.
- Weekend & Holiday In-Time: 10:00 PM.
- Night Out / Leave Pass: Students wishing to stay outside or visit home must apply for an e-Gatepass on the College App at least 24 hours in advance with parent SMS confirmation.
- Late Entry Fine: First late entry attracts a warning; subsequent late entries incur a Rs. 200 fine and notification to guardians.

2. HOSTEL MESS SCHEDULE
- Breakfast: 7:30 AM to 9:00 AM
- Lunch: 12:00 PM to 2:00 PM
- Evening Tea & Snacks: 5:00 PM to 6:00 PM
- Dinner: 7:30 PM to 9:30 PM
- Special dietary requests or complaints can be submitted to the Student Mess Committee on the 1st of every month.

3. CAMPUS WI-FI & INTERNET ACCESS
- Network SSID: Campus_Student_5G (Academic blocks) and Hostel_Net (Residences).
- Login Credentials: Username is your Student Registration ID; initial password is DOB (DDMMYYYY), change on first login.
- Bandwidth Quota: 10 GB per day per student at speeds up to 100 Mbps.
- Restricted Content: BitTorrent clients, pirated streaming, and offensive content are blocked by the firewall.

4. MEDICAL CENTRE & EMERGENCY CONTACTS
- Campus Health Centre is open 24x7 with resident nurses on duty.
- Visiting Chief Medical Officer timings: 9:00 AM - 1:00 PM and 4:30 PM - 7:30 PM.
- 24x7 Emergency Ambulance: Call extension 911 from any campus intercom or mobile +91-9876543210.
- Free basic consultation and essential medicines are provided to all enrolled students with valid ID cards.

5. ZERO TOLERANCE ANTI-RAGGING POLICY
- Ragging in any form (verbal, physical, psychological) is strictly prohibited as per Supreme Court of India directives.
- Penalties include immediate suspension, cancellation of admission, and lodging of police FIR.
- National Anti-Ragging Helpline (Toll-Free): 1800-180-5522 (24x7)
- Campus Anti-Ragging Squad Email: antiragging@college.edu / Phone: +91-11-2345-6799
"""
    },
    {
        "category": "Scholarships",
        "category_desc": "Merit scholarships, need-based fee waivers, and financial assistance schemes",
        "title": "Scholarships, Fee Waivers, and Financial Assistance",
        "filename": "Scholarships_Fee_Waivers_and_Financial_Assistance.txt",
        "description": "Details about Academic Merit Scholarships, EWS fee waivers, Sports scholarships, and application procedures.",
        "content": """SCHOLARSHIP & FINANCIAL AID SCHEMES
OFFICE OF STUDENT FINANCIAL SERVICES

1. MERIT SCHOLARSHIP SCHEME
- University Rank 1st (Branch Topper): 100% Tuition Fee Waiver for the subsequent academic year, requiring CGPA >= 9.50 with no backlogs.
- University Rank 2nd & 3rd: 50% Tuition Fee Waiver, requiring CGPA >= 9.00.
- Dean's Honour List: Students maintaining CGPA >= 8.50 receive a merit certificate and a one-time cash award of Rs. 10,000 at the Annual Convocation.

2. NEED-BASED / ECONOMICALLY WEAKER SECTION (EWS) ASSISTANCE
- Eligibility: Annual family gross income from all sources less than Rs. 2,50,000 per annum.
- Benefits: Up to 75% waiver on tuition fees and subsidized hostel accommodation.
- Required Documents:
  1. Valid Income Certificate issued by Revenue Authority (Tehsildar / Sub-Divisional Magistrate).
  2. Income Tax Return (ITR-V) or Form 16 of earning parents for previous financial year.
  3. Copy of previous academic semester marksheet with CGPA >= 7.00.

3. SPORTS & CULTURAL EXCELLENCE SCHOLARSHIPS
- International / National Level Players: 100% tuition waiver and customized academic scheduling for training camps.
- State / Inter-University Medalists: Rs. 25,000 cash grant per semester plus free campus gym and sports facilities.

4. APPLICATION WINDOW & PROCEDURE
- Applications open during the first 3 weeks of every semester on the ERP Scholarship portal.
- Physical verification of documents takes place at the Scholarship Desk, Ground Floor, Admin Block.
- Inquiries: scholarships@college.edu | Tel: +91-11-2345-6712
"""
    },
    {
        "category": "Library & Labs",
        "category_desc": "Central library access, digital journals, research databases, and computer labs",
        "title": "Central Library and Computing Laboratory Guidelines",
        "filename": "Central_Library_and_Computing_Laboratory_Guidelines.txt",
        "description": "Library book borrowing limits, overdue fines, IEEE/Springer journal access, and computer lab hours.",
        "content": """CENTRAL LIBRARY AND COMPUTING INFRASTRUCTURE GUIDELINES
KNOWLEDGE RESOURCE CENTRE

1. LIBRARY TIMINGS
- Regular Working Days: 8:00 AM to 10:00 PM
- Sundays & College Holidays: 9:00 AM to 5:00 PM
- 24x7 Reading Hall: Open round-the-clock during Mid-Term and End-Semester examination weeks.

2. BORROWING PRIVILEGES & OVERDUE CHARGES
- Undergraduate Students (B.Tech / B.Sc / BCA): 4 books at a time for up to 14 days. Renewal allowed twice if not reserved by another user.
- Postgraduate Students (M.Tech / MBA / MCA): 6 books at a time for up to 21 days.
- Overdue Fine: Rs. 5 per day per book for the first 7 days of delay; Rs. 10 per day thereafter.
- Book Bank Scheme: Economically disadvantaged students can borrow full-semester textbooks free of charge for the entire duration of the semester.

3. DIGITAL LIBRARY & E-RESOURCES
- Subscribed Databases: IEEE Xplore, ScienceDirect, ACM Digital Library, SpringerLink, and JSTOR.
- Remote Access: Available through the MyLOFT / EZproxy portal using your institutional @college.edu Google email address.
- Plagiarism Checking: Students can get their final year project reports checked for similarity via Turnitin at the Library Reference Section (Desk 3).

4. COMPUTING LABS & SOFTWARE TOOLS
- Advanced Computing Labs (Labs 1-6) operate from 8:30 AM to 8:30 PM on weekdays.
- Licensed software packages available: MATLAB, AutoCAD, SolidWorks, Oracle 19c, Android Studio, and Visual Studio Code with Python 3.12 / Java 21 environments.
- High-Performance Computing (HPC) GPU Cluster: Available for final year research projects upon recommendation from the project faculty guide.
"""
    }
]


class Command(BaseCommand):
    help = "Load realistic college documents into the database and index them into ChromaDB for RAG"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reindex',
            action='store_true',
            help='Force re-index even if document title already exists',
        )

    def handle(self, *args, **options):
        force_reindex = options['reindex']

        # Get or select an admin user as uploader
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            admin_user = User.objects.first()

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Loading Sample College Documents ==="))
        self.stdout.write(f"Assigned uploader: {admin_user.username if admin_user else 'None'}\n")

        created_count = 0
        indexed_count = 0

        for doc_info in SAMPLE_DOCS:
            # 1. Create or get Category
            category, _ = DocumentCategory.objects.get_or_create(
                name=doc_info["category"],
                defaults={"description": doc_info["category_desc"], "is_active": True}
            )

            # 2. Check if Document already exists
            doc = Document.objects.filter(title=doc_info["title"]).first()

            if not doc:
                content_bytes = doc_info["content"].strip().encode("utf-8")
                content_file = ContentFile(content_bytes, name=doc_info["filename"])

                doc = Document.objects.create(
                    title=doc_info["title"],
                    description=doc_info["description"],
                    file=content_file,
                    category=category,
                    uploaded_by=admin_user,
                    file_type=Document.FILE_TYPE_TXT,
                    file_size=len(content_bytes),
                    is_active=True,
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [+] Created: {doc.title}"))
            else:
                self.stdout.write(f"  [*] Already exists: {doc.title}")

            # 3. Index into ChromaDB if not indexed or force reindex
            if force_reindex or not doc.is_indexed:
                res = process_document(doc)
                if res.get("status") == "success":
                    indexed_count += 1
                    self.stdout.write(self.style.SUCCESS(f"      -> Indexed {res.get('chunk_count', 0)} chunks into ChromaDB"))
                else:
                    self.stdout.write(self.style.ERROR(f"      -> Indexing failed: {res.get('message')}"))
            else:
                self.stdout.write(f"      -> Already indexed")

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(
            f"Summary: {created_count} documents created, {indexed_count} indexed."
        ))

        try:
            from chat.services.rag_service import get_vectordb
            col = get_vectordb()
            self.stdout.write(self.style.SUCCESS(f"ChromaDB total indexed chunks: {col.count()}\n"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not check ChromaDB count: {e}\n"))
