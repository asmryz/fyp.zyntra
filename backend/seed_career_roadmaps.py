"""
Career roadmap content for BS Computer Science and BS Software Engineering.

Run from the backend folder (virtual environment active):
    python seed_career_roadmaps.py

What it does, in ONE transaction (nothing is saved if any step fails):
  - finds each program by its slug and the roadmap already linked to it
    (a roadmap is inserted only if the program has none), and sets the
    roadmap's title and description;
  - for each career domain (roadmap_branches): reuses a branch with the same
    name in that roadmap or inserts it; sets description (with the relevant
    SZABIST courses), colour and position;
  - for each job role (roadmap_nodes): reuses a step with the same title in
    that branch or inserts it, then replaces that step's detail sections.
Running it again updates the same rows, so it never creates duplicates.

Detail sections use the section types the application already supports
(constants.ROADMAP_SECTION_TYPES), so they display in the student roadmap and
can still be edited and saved from the admin/staff roadmap editor:
    Job Description                  -> text   {"text": ...}
    Technical Skills                 -> skills {"items": [...]}
    Soft Skills                      -> list   {"items": [...]}
    Additional Technologies to Learn -> list   {"items": ["Name: purpose", ...]}
Every section is validated with the API's RoadmapSectionIn schema before insert.

Course titles and codes are copied from the SZABIST Prospectus 2025-26
(Faculty of Computing and Engineering Sciences: BS Computer Science and
BS Software Engineering course plans, CS Electives and SE Electives). Elective
availability varies by semester, as the prospectus itself notes.
"""
import json

from sqlalchemy import text

from database import SessionLocal
from app.schemas.content import RoadmapBranchIn, RoadmapSectionIn

ELECTIVE_NOTE = "Elective availability varies by semester (SZABIST Prospectus 2025-26)."


def courses_text(core, electives):
    return (
        "Relevant SZABIST courses (Prospectus 2025-26):\n\n"
        f"Core courses: {'; '.join(core)}.\n\n"
        f"Electives: {'; '.join(electives)}.\n\n"
        f"{ELECTIVE_NOTE}"
    )


def role(title, description, technical, soft, tools):
    return {"title": title, "description": description, "technical": technical, "soft": soft, "tools": tools}


# ---------------------------------------------------------------- BS Computer Science

BSCS = {
    "slug": "bs-computer-science",
    "title": "BS Computer Science Career Roadmap",
    "description": (
        "Explore career opportunities available through a Bachelor's degree in Computer Science. Discover different "
        "computing domains, relevant university courses and electives, potential job roles, required skills, and "
        "additional technologies to learn for professional development."
    ),
    "domains": [
        {
            "name": "Full-Stack Development",
            # None keeps the description already entered from the dashboard; the course list is added after it
            "description": None,
            "color": "#2563EB",
            "core": [
                "CSC 1103 Fundamentals of Programming", "CSC 1208 Object Oriented Programming Techniques",
                "CSC 2102 Data Structures and Algorithms", "CSC 2203 Database Systems",
                "CSC 3108 Advance Database Management Systems", "CSC 3109 Software Engineering",
                "CSC 3209 Computer Networks", "CSC 3106 HCI & Computer Graphics",
            ],
            "electives": [
                "CSC 4717 Web Technologies-I", "CSC 4817 Web Technologies-II", "CSC 4724 User Interface Design",
                "CSC 4823 Interaction Design", "CSC 4827 Software Quality Engineering and Testing",
                "CSC 4721 Introduction to Cloud Computing",
            ],
            "roles": [
                role(
                    "Frontend Developer",
                    "Frontend Developers build the parts of web applications that users see and interact with. They "
                    "turn designs into responsive, accessible pages, connect the interface to backend APIs, manage "
                    "application state and make sure pages load quickly and work across browsers and devices.",
                    ["HTML5 and semantic markup", "CSS3, Flexbox and CSS Grid", "JavaScript (ES6+)", "TypeScript",
                     "React or Angular", "Responsive and mobile-first design", "Consuming REST APIs",
                     "Web accessibility (WCAG)", "Git version control", "Browser developer tools and debugging"],
                    ["Attention to visual detail", "Collaboration with designers and backend developers",
                     "Clear communication", "Problem solving", "Openness to feedback"],
                    [("Tailwind CSS", "Utility-first CSS framework for building consistent layouts quickly"),
                     ("Next.js", "React framework for server-side rendering, routing and better SEO"),
                     ("Figma", "Reading design files and handing off measurements, colours and assets"),
                     ("Vite", "Fast build tool and development server for modern frontend projects"),
                     ("Jest and React Testing Library", "Writing unit and component tests for user interfaces")],
                ),
                role(
                    "Backend Developer",
                    "Backend Developers build the server-side logic that powers applications. They design APIs, model "
                    "and query databases, implement authentication and business rules, and make services secure, "
                    "reliable and able to handle growing numbers of users.",
                    ["Server-side programming (Node.js, Python or Java)", "RESTful API design", "SQL and relational database design",
                     "Authentication and authorization (sessions, JWT, OAuth)", "Data structures and algorithms",
                     "Error handling and logging", "Caching strategies", "Git version control", "Unit and integration testing"],
                    ["Analytical thinking", "Attention to detail", "Documentation writing", "Teamwork", "Ownership and reliability"],
                    [("PostgreSQL", "Production-grade relational database for storing application data"),
                     ("Express.js or FastAPI", "Frameworks for building web APIs quickly in Node.js or Python"),
                     ("Redis", "In-memory store used for caching, sessions and queues"),
                     ("Docker", "Packaging services and their dependencies so they run the same everywhere"),
                     ("Postman", "Designing, testing and documenting API requests")],
                ),
                role(
                    "Full-Stack Developer",
                    "Full-Stack Developers work across the whole application: the user interface, the server-side APIs "
                    "and the database. They deliver complete features end to end, decide how data flows between "
                    "layers and deploy working applications for real users.",
                    ["Frontend development with HTML, CSS, JavaScript and React", "Backend development with Node.js or Python",
                     "REST API design and integration", "Relational and NoSQL databases", "Authentication and security basics",
                     "Git and collaborative workflows", "Application deployment", "Debugging across the stack"],
                    ["Adaptability", "Time management", "Communication with technical and non-technical people",
                     "Independent learning", "Product thinking"],
                    [("MongoDB", "Document database for flexible, JSON-like data"),
                     ("Docker", "Containerising the frontend, backend and database for consistent environments"),
                     ("GitHub Actions", "Automating tests and deployments on every code change"),
                     ("Vercel or Render", "Hosting platforms for deploying web applications and APIs"),
                     ("Prisma or SQLAlchemy", "ORMs that map database tables to code and manage migrations")],
                ),
            ],
        },
        {
            "name": "Artificial Intelligence & Machine Learning",
            "description": (
                "Artificial Intelligence and Machine Learning focus on building systems that learn from data to make "
                "predictions, recognise patterns, understand images and language, and automate decisions. The domain "
                "combines programming with mathematics, statistics and algorithm design."
            ),
            "color": "#16A34A",
            "core": [
                "CSC 3206 Artificial Intelligence", "CSC 1206 Probability and Statistics", "CSC 2206 Linear Algebra",
                "CSC 1202 Multivariate Calculus", "CSC 2102 Data Structures and Algorithms",
                "CSC 3202 Design and Analysis of Algorithms",
            ],
            "electives": [
                "CSC 4703 Applied Data Mining", "CSC 4706 Digital Image Processing", "CSC 4826 Introduction to Data Sciences",
            ],
            "roles": [
                role(
                    "Junior Machine Learning Engineer",
                    "Junior Machine Learning Engineers prepare data, train and evaluate machine learning models and help "
                    "move them into production. They work with senior engineers to improve model accuracy, monitor "
                    "performance and package models so applications can use them.",
                    ["Python programming", "NumPy and pandas", "Supervised and unsupervised learning", "scikit-learn",
                     "Model evaluation metrics and cross-validation", "Feature engineering", "Linear algebra and statistics",
                     "Neural network basics", "Git version control"],
                    ["Curiosity and experimentation", "Analytical thinking", "Clear reporting of results", "Patience", "Teamwork"],
                    [("PyTorch", "Deep learning framework for building and training neural networks"),
                     ("TensorFlow and Keras", "Alternative deep learning framework with high-level model APIs"),
                     ("Jupyter Notebook", "Interactive environment for data exploration and experiments"),
                     ("MLflow", "Tracking experiments, parameters and model versions"),
                     ("Hugging Face", "Hub of pre-trained models and datasets for transfer learning")],
                ),
                role(
                    "AI Application Developer",
                    "AI Application Developers build software products that use AI features such as chatbots, "
                    "recommendations, document understanding and smart search. They integrate pre-trained models and AI "
                    "APIs into web or mobile applications and make the results reliable and useful for users.",
                    ["Python or JavaScript programming", "Calling and integrating AI model APIs", "Prompt design for large language models",
                     "REST API development", "Working with text, image and JSON data", "Basic machine learning concepts",
                     "Evaluating and testing AI outputs", "Handling user data responsibly"],
                    ["User-focused thinking", "Creativity", "Ethical judgement", "Communication", "Problem solving"],
                    [("LangChain", "Framework for building applications that chain language-model calls and tools"),
                     ("Vector databases (e.g. Pinecone, pgvector)", "Storing embeddings for semantic search and retrieval-augmented generation"),
                     ("FastAPI", "Serving AI features through fast Python web APIs"),
                     ("Streamlit", "Building quick interactive demos of AI applications"),
                     ("Hugging Face Transformers", "Using pre-trained language and vision models in code")],
                ),
                role(
                    "Computer Vision Developer",
                    "Computer Vision Developers build systems that understand images and video, such as object "
                    "detection, face recognition, document scanning and quality inspection. They process visual data, "
                    "train or fine-tune vision models and optimise them to run on servers, cameras or mobile devices.",
                    ["Python programming", "Image processing fundamentals", "OpenCV", "Convolutional neural networks",
                     "Object detection and segmentation", "Data annotation and augmentation", "Linear algebra",
                     "Model evaluation (precision, recall, IoU)"],
                    ["Attention to detail", "Persistence when debugging", "Research skills", "Analytical thinking", "Teamwork"],
                    [("YOLO (Ultralytics)", "Real-time object detection models that can be trained on custom data"),
                     ("PyTorch / torchvision", "Building and training vision models with ready-made architectures"),
                     ("Label Studio", "Annotating images and videos to create training datasets"),
                     ("ONNX Runtime", "Running trained models efficiently on different hardware"),
                     ("OpenCV DNN module", "Running deep learning models inside image processing pipelines")],
                ),
            ],
        },
        {
            "name": "Data Science & Analytics",
            "description": (
                "Data Science and Analytics turn raw data into insights that guide decisions. The domain covers "
                "collecting, cleaning and storing data, analysing it with statistics, building predictive models and "
                "presenting findings through reports and dashboards."
            ),
            "color": "#9333EA",
            "core": [
                "CSC 1206 Probability and Statistics", "CSC 2206 Linear Algebra", "CSC 2203 Database Systems",
                "CSC 3108 Advance Database Management Systems", "CSC 3206 Artificial Intelligence",
                "CSC 4106 Parallel and Distributed Computing",
            ],
            "electives": [
                "CSC 4826 Introduction to Data Sciences", "CSC 4703 Applied Data Mining", "CSC 4708 Enterprise Resource Planning",
            ],
            "roles": [
                role(
                    "Data Analyst",
                    "Data Analysts collect, clean and analyse data to answer business questions. They write queries, "
                    "find trends, build dashboards and reports, and explain what the numbers mean so managers can make "
                    "informed decisions.",
                    ["SQL querying (joins, aggregations, window functions)", "Microsoft Excel (pivot tables, lookups)",
                     "Descriptive statistics", "Data cleaning and preparation", "Data visualisation",
                     "Python with pandas", "Dashboard design", "Defining and tracking KPIs"],
                    ["Business understanding", "Storytelling with data", "Attention to detail", "Curiosity", "Presentation skills"],
                    [("Power BI", "Building interactive business dashboards and reports"),
                     ("Tableau", "Visual analytics tool for exploring and sharing data"),
                     ("Google Looker Studio", "Free tool for web-based reports connected to many data sources"),
                     ("Jupyter Notebook", "Documenting analysis steps with code, charts and notes"),
                     ("Git", "Versioning SQL scripts and analysis notebooks")],
                ),
                role(
                    "Junior Data Scientist",
                    "Junior Data Scientists use statistics and machine learning to find patterns and make predictions "
                    "from data. They explore datasets, run experiments, build and validate models, and communicate "
                    "results to technical and business teams.",
                    ["Python (pandas, NumPy)", "Statistics and hypothesis testing", "Machine learning with scikit-learn",
                     "Exploratory data analysis", "Feature engineering", "SQL", "Data visualisation (Matplotlib, Seaborn)",
                     "Model validation"],
                    ["Critical thinking", "Communicating findings clearly", "Curiosity", "Business awareness", "Teamwork"],
                    [("Kaggle", "Practising on real datasets and learning from competition solutions"),
                     ("XGBoost / LightGBM", "High-performance gradient boosting for tabular data"),
                     ("Plotly", "Interactive charts for exploring and presenting results"),
                     ("Statsmodels", "Statistical modelling and hypothesis tests in Python"),
                     ("MLflow", "Tracking experiments and comparing model versions")],
                ),
                role(
                    "Junior Data Engineer",
                    "Junior Data Engineers build and maintain the pipelines that move data from source systems into "
                    "databases and data warehouses. They make sure data is clean, reliable and available on time for "
                    "analysts, data scientists and applications.",
                    ["Advanced SQL", "Python scripting", "Data modelling (star and snowflake schemas)",
                     "ETL / ELT pipeline development", "Relational databases", "Data quality checks",
                     "Linux command line", "Basics of distributed data processing"],
                    ["Reliability and ownership", "Problem solving", "Documentation", "Collaboration with analysts", "Attention to detail"],
                    [("Apache Airflow", "Scheduling and monitoring data pipelines"),
                     ("Apache Spark", "Processing large datasets in parallel across a cluster"),
                     ("dbt", "Transforming data inside the warehouse using tested SQL models"),
                     ("Apache Kafka", "Streaming data between systems in real time"),
                     ("Snowflake or BigQuery", "Cloud data warehouses for analytics at scale")],
                ),
            ],
        },
        {
            "name": "Cybersecurity",
            "description": (
                "Cybersecurity protects systems, networks and data from attacks and misuse. The domain covers "
                "monitoring for threats, finding and fixing vulnerabilities, responding to incidents and applying "
                "security policies that keep organisations safe and compliant."
            ),
            "color": "#EA580C",
            "core": [
                "CSC 4107 Information Security", "CSC 3209 Computer Networks", "CSC 3107 Operating Systems",
                "CSC 3105 Computer Organization and Assembly Language", "CSC 4109 Professional Practices",
            ],
            "electives": [
                "CSC 4714 Network Security and Encryption", "CSC 4805 Data and Network Security", "CSC 4808 Ethical Hacking",
                "CSC 4803 Auditing Information Systems", "CSC 4726 Systems and Network Administration",
                "CSC 4722 Introduction to Blockchain Technology",
            ],
            "roles": [
                role(
                    "SOC Analyst",
                    "Security Operations Centre (SOC) Analysts monitor an organisation's systems for suspicious "
                    "activity. They review security alerts, investigate possible incidents, escalate real threats and "
                    "help contain and document attacks.",
                    ["Networking fundamentals (TCP/IP, DNS, HTTP)", "Log analysis", "SIEM alert triage", "Windows and Linux administration basics",
                     "Malware and phishing analysis basics", "Incident response process", "MITRE ATT&CK framework",
                     "Firewalls and intrusion detection"],
                    ["Calm under pressure", "Attention to detail", "Clear incident reporting", "Teamwork in shifts", "Ethical conduct"],
                    [("Splunk", "Searching and correlating logs to detect security events"),
                     ("Wireshark", "Capturing and inspecting network traffic"),
                     ("Microsoft Sentinel", "Cloud-based SIEM for collecting and analysing alerts"),
                     ("Security Onion", "Open-source platform for network security monitoring"),
                     ("CompTIA Security+", "Entry-level certification that validates core security knowledge")],
                ),
                role(
                    "Junior Penetration Tester",
                    "Junior Penetration Testers are authorised to attack systems, web applications and networks to "
                    "find security weaknesses before real attackers do. They follow a defined scope, document every "
                    "finding and explain how to fix each vulnerability.",
                    ["Networking and protocols", "Linux command line", "Web application vulnerabilities (OWASP Top 10)",
                     "Reconnaissance and scanning", "Exploitation basics", "Scripting in Python or Bash",
                     "Password and authentication attacks", "Writing penetration test reports"],
                    ["Ethical responsibility", "Persistence", "Creative thinking", "Clear technical writing", "Respect for scope and rules"],
                    [("Kali Linux", "Linux distribution with the standard penetration testing toolset"),
                     ("Burp Suite", "Intercepting and testing web application traffic"),
                     ("Nmap", "Discovering hosts, open ports and running services"),
                     ("Metasploit", "Framework for testing known exploits in a controlled way"),
                     ("TryHackMe / Hack The Box", "Legal practice labs for building hands-on skills")],
                ),
                role(
                    "Information Security Analyst",
                    "Information Security Analysts protect an organisation's information by assessing risks, applying "
                    "security controls and policies, managing access and checking compliance. They also help with "
                    "audits, awareness training and incident handling.",
                    ["Risk assessment", "Security policies and controls", "Identity and access management",
                     "Vulnerability management", "Encryption and key management basics", "Security audits and compliance",
                     "Network security", "Backup and disaster recovery planning"],
                    ["Communication with management", "Analytical thinking", "Integrity", "Documentation", "Training and awareness skills"],
                    [("Nessus", "Scanning systems for known vulnerabilities"),
                     ("ISO/IEC 27001", "International standard for information security management"),
                     ("NIST Cybersecurity Framework", "Structured approach to identifying and managing security risk"),
                     ("Microsoft Entra ID", "Managing user identities, access and multi-factor authentication"),
                     ("OpenVAS", "Open-source vulnerability scanner")],
                ),
            ],
        },
        {
            "name": "Cloud Computing & DevOps",
            "description": (
                "Cloud Computing and DevOps focus on running software reliably at scale. The domain covers cloud "
                "infrastructure, automation of builds and deployments, containers, monitoring and the practices that "
                "let development and operations teams release changes quickly and safely."
            ),
            "color": "#DB2777",
            "core": [
                "CSC 3107 Operating Systems", "CSC 3209 Computer Networks", "CSC 4106 Parallel and Distributed Computing",
                "CSC 3109 Software Engineering",
            ],
            "electives": [
                "CSC 4721 Introduction to Cloud Computing", "CSC 4725 Introduction to Development and Operations",
                "CSC 4726 Systems and Network Administration", "CSC 4716 Switching and Routing",
            ],
            "roles": [
                role(
                    "Cloud Engineer",
                    "Cloud Engineers design, build and manage infrastructure on cloud platforms. They set up servers, "
                    "networks, storage and databases in the cloud, control access and costs, and keep applications "
                    "secure and available.",
                    ["Cloud platform fundamentals (AWS, Azure or Google Cloud)", "Linux administration", "Virtual networks, subnets and firewalls",
                     "Identity and access management", "Cloud storage and managed databases", "Infrastructure as code basics",
                     "Scripting in Bash or Python", "Cost monitoring"],
                    ["Planning and organisation", "Problem solving", "Documentation", "Security awareness", "Collaboration"],
                    [("Terraform", "Defining cloud infrastructure as reusable code"),
                     ("AWS Certified Cloud Practitioner", "Entry-level certification covering core AWS services"),
                     ("Azure Fundamentals (AZ-900)", "Entry-level certification for Microsoft Azure"),
                     ("Docker", "Packaging applications into containers for cloud deployment"),
                     ("CloudWatch / Azure Monitor", "Monitoring cloud resources and setting alerts")],
                ),
                role(
                    "DevOps Engineer",
                    "DevOps Engineers automate how software is built, tested and deployed. They create CI/CD pipelines, "
                    "manage containers and infrastructure, and work with developers so that new features reach users "
                    "quickly without breaking production.",
                    ["Linux and shell scripting", "Git and branching strategies", "CI/CD pipeline design", "Docker containers",
                     "Kubernetes basics", "Infrastructure as code", "Monitoring and logging", "Networking fundamentals"],
                    ["Collaboration between teams", "Automation mindset", "Troubleshooting under pressure", "Continuous learning", "Clear communication"],
                    [("GitHub Actions / GitLab CI", "Automating builds, tests and deployments"),
                     ("Kubernetes", "Orchestrating containers across many servers"),
                     ("Ansible", "Automating server configuration"),
                     ("Prometheus", "Collecting metrics from applications and servers"),
                     ("Grafana", "Visualising metrics on dashboards")],
                ),
                role(
                    "Site Reliability Engineer",
                    "Site Reliability Engineers (SREs) keep production systems fast and available. They define "
                    "reliability targets, build monitoring and alerting, automate repetitive operations work, respond "
                    "to outages and lead post-incident reviews to prevent repeats.",
                    ["Linux internals", "Programming in Python or Go", "Monitoring, alerting and observability",
                     "Service level objectives (SLOs) and error budgets", "Incident response", "Load balancing and caching",
                     "Distributed systems fundamentals", "Capacity planning"],
                    ["Calm decision-making during incidents", "Analytical thinking", "Blameless communication", "Ownership", "Documentation"],
                    [("Prometheus and Alertmanager", "Collecting metrics and sending alerts when limits are breached"),
                     ("Grafana", "Building reliability and performance dashboards"),
                     ("OpenTelemetry", "Collecting traces, metrics and logs in a standard way"),
                     ("PagerDuty", "Managing on-call schedules and incident escalation"),
                     ("Kubernetes", "Running and scaling containerised services")],
                ),
            ],
        },
        {
            "name": "Mobile App Development",
            "description": (
                "Mobile App Development focuses on building applications for smartphones and tablets. The domain "
                "covers native and cross-platform development, mobile user interface design, working with device "
                "features and APIs, and publishing apps to app stores."
            ),
            "color": "#DC2626",
            "core": [
                "CSC 1208 Object Oriented Programming Techniques", "CSC 2102 Data Structures and Algorithms",
                "CSC 2203 Database Systems", "CSC 3106 HCI & Computer Graphics", "CSC 3109 Software Engineering",
            ],
            "electives": [
                "CSC 4802 Android Application Development", "CSC 4727 Hybrid Mobile Application Development",
                "CSC 4724 User Interface Design", "CSC 4823 Interaction Design",
            ],
            "roles": [
                role(
                    "Android Developer",
                    "Android Developers build native applications for Android phones and tablets. They create screens "
                    "and navigation, connect apps to APIs and local storage, use device features such as the camera and "
                    "location, and publish and maintain apps on the Google Play Store.",
                    ["Kotlin", "Java", "Android SDK and Android Studio", "Jetpack Compose and XML layouts",
                     "Activity and app lifecycle", "Local storage with Room / SQLite", "Consuming REST APIs",
                     "MVVM architecture", "Debugging and performance profiling"],
                    ["User empathy", "Attention to detail", "Problem solving", "Teamwork", "Adaptability to platform changes"],
                    [("Retrofit", "Type-safe HTTP client for calling REST APIs"),
                     ("Firebase", "Authentication, cloud database, analytics and push notifications"),
                     ("Hilt", "Dependency injection for cleaner, testable Android code"),
                     ("Google Play Console", "Publishing, testing and monitoring Android apps"),
                     ("Espresso", "Automated UI testing for Android apps")],
                ),
                role(
                    "Cross-Platform Mobile Developer",
                    "Cross-Platform Mobile Developers build one codebase that runs on both Android and iOS. They "
                    "create shared user interfaces and logic, integrate native device features when needed and release "
                    "apps to both app stores.",
                    ["Flutter with Dart or React Native with JavaScript", "State management", "Responsive mobile layouts",
                     "REST API integration", "Local storage", "Native module and plugin integration",
                     "App store build and release process", "Git version control"],
                    ["Adaptability", "Communication", "Time management", "Problem solving", "User-centred thinking"],
                    [("Flutter", "Google's UI toolkit for building Android and iOS apps from one Dart codebase"),
                     ("React Native", "Building native mobile apps with JavaScript and React"),
                     ("Expo", "Tooling that speeds up React Native development and builds"),
                     ("Firebase", "Backend services such as authentication, database and messaging"),
                     ("Codemagic / EAS Build", "Automating mobile builds and releases")],
                ),
                role(
                    "Mobile UI Developer",
                    "Mobile UI Developers specialise in the look, feel and usability of mobile apps. They turn designs "
                    "into smooth, accessible screens, build reusable UI components and animations, and make sure "
                    "interfaces work well on different screen sizes.",
                    ["Mobile UI frameworks (Jetpack Compose, SwiftUI or Flutter widgets)", "Material Design and Human Interface Guidelines",
                     "Responsive layouts for different screen sizes", "Animations and transitions", "Mobile accessibility",
                     "Reusable component design", "Basic usability testing"],
                    ["Visual design sense", "Attention to detail", "Collaboration with designers", "Openness to feedback", "Empathy for users"],
                    [("Figma", "Inspecting designs and prototypes for implementation"),
                     ("Lottie", "Adding lightweight vector animations to apps"),
                     ("Material Design 3", "Google's design system for consistent Android interfaces"),
                     ("Storybook", "Building and reviewing UI components in isolation"),
                     ("Accessibility Scanner", "Finding accessibility issues in Android apps")],
                ),
            ],
        },
    ],
}

# ---------------------------------------------------------------- BS Software Engineering

BSSE = {
    "slug": "bs-software-engineering",
    "title": "BS Software Engineering Career Roadmap",
    "description": (
        "Explore career opportunities available through a Bachelor's degree in Software Engineering. Discover software "
        "development, architecture, quality assurance, mobile applications, cloud technologies, and intelligent "
        "applications, along with relevant university courses, potential job roles, required skills, and additional "
        "technologies to learn."
    ),
    "domains": [
        {
            "name": "Web & Application Development",
            "description": (
                "Web and Application Development focuses on building the web and desktop applications people use "
                "every day. The domain covers turning requirements into working features, building user interfaces, "
                "connecting them to data and following a disciplined software construction process."
            ),
            "color": "#2563EB",
            "core": [
                "CSC 1103 Fundamentals of Programming", "CSC 1208 Object Oriented Programming Techniques",
                "CSC 2203 Database Systems", "SEC 2407 Software Requirement Engineering",
                "SEC 3604 Software Construction and Development",
            ],
            "electives": [
                "SEC 4518 Visual Programming", "SEC 4549 User Interface Design", "SEC 4511 e-Commerce",
                "SEC 4526 Design Patterns", "SEC 4539 Semantic Web",
            ],
            "roles": [
                role(
                    "Frontend Developer",
                    "Frontend Developers build the user-facing side of web applications. They implement designs as "
                    "responsive, accessible interfaces, connect them to backend services and keep the user experience "
                    "fast and consistent across browsers.",
                    ["HTML5 and CSS3", "JavaScript (ES6+) and TypeScript", "React or Angular", "Responsive design",
                     "Consuming REST APIs", "Web accessibility", "Component-based architecture", "Git version control"],
                    ["Attention to detail", "Collaboration with designers", "Communication", "Problem solving", "Openness to feedback"],
                    [("Tailwind CSS", "Utility-first CSS framework for consistent styling"),
                     ("Next.js", "React framework for routing and server-side rendering"),
                     ("Figma", "Working from design files and prototypes"),
                     ("Cypress", "End-to-end testing of web interfaces in the browser"),
                     ("Storybook", "Developing and documenting UI components in isolation")],
                ),
                role(
                    "Web Application Developer",
                    "Web Application Developers build complete business web applications such as portals, booking "
                    "systems and online stores. They gather requirements, design data models, implement features on "
                    "the client and server, and maintain the application after release.",
                    ["A web framework (Django, Laravel, ASP.NET Core or Express.js)", "HTML, CSS and JavaScript",
                     "Relational databases and SQL", "MVC architecture", "Forms, validation and authentication",
                     "Web security basics (OWASP Top 10)", "Requirements analysis", "Git version control"],
                    ["Client communication", "Analytical thinking", "Time management", "Teamwork", "Responsibility for quality"],
                    [("Django or Laravel", "Full-featured frameworks with built-in admin, ORM and authentication"),
                     ("PostgreSQL / MySQL", "Relational databases for application data"),
                     ("Docker", "Running the application and its database consistently in every environment"),
                     ("Postman", "Testing and documenting the application's APIs"),
                     ("Stripe or other payment APIs", "Adding secure online payments to web applications")],
                ),
                role(
                    "Full-Stack Developer",
                    "Full-Stack Developers deliver features across the frontend, backend and database. They design "
                    "APIs, build interfaces, manage data and deploy applications, taking responsibility for a "
                    "feature from requirement to release.",
                    ["Frontend development with React", "Backend development with Node.js, Python or Java", "REST API design",
                     "Relational and NoSQL databases", "Authentication and authorization", "Testing across the stack",
                     "Deployment and environment configuration", "Git workflows"],
                    ["Adaptability", "Ownership", "Communication", "Independent learning", "Product thinking"],
                    [("Docker", "Containerising every part of the stack"),
                     ("GitHub Actions", "Running tests and deployments automatically"),
                     ("MongoDB", "Document database for flexible data"),
                     ("Prisma or TypeORM", "ORMs for type-safe database access and migrations"),
                     ("Vercel / Render", "Hosting for frontend applications and APIs")],
                ),
            ],
        },
        {
            "name": "Backend Engineering & Software Architecture",
            "description": (
                "Backend Engineering and Software Architecture focus on the server-side systems behind applications "
                "and on how large software is structured. The domain covers APIs, data storage, performance, "
                "scalability and the design decisions that keep systems maintainable as they grow."
            ),
            "color": "#16A34A",
            "core": [
                "SEC 2406 Software Design and Architecture", "SEC 3604 Software Construction and Development",
                "CSC 2102 Data Structures and Algorithms", "CSC 3202 Design and Analysis of Algorithms",
                "CSC 2203 Database Systems", "CSC 3107 Operating Systems", "CSC 3209 Computer Networks",
                "CSC 4106 Parallel and Distributed Computing",
            ],
            "electives": [
                "SEC 4526 Design Patterns", "SEC 4543 Systems Programming", "SEC 4538 Real Time Systems",
                "SEC 4529 Global Software Development", "SEC 4519 Software Engineering Economics",
            ],
            "roles": [
                role(
                    "Backend Developer",
                    "Backend Developers build the APIs, business logic and data layers that applications depend on. "
                    "They model databases, secure endpoints, integrate external services and make sure the server "
                    "side performs well under load.",
                    ["Server-side language (Java, C#, Python or Node.js)", "REST API design", "SQL and database design",
                     "Authentication and authorization", "Caching", "Asynchronous processing and message queues",
                     "Unit and integration testing", "Git version control"],
                    ["Analytical thinking", "Attention to detail", "Documentation", "Teamwork", "Reliability"],
                    [("Spring Boot", "Java framework for production-ready backend services"),
                     ("ASP.NET Core", "Microsoft framework for building web APIs in C#"),
                     ("Redis", "In-memory caching and session storage"),
                     ("RabbitMQ", "Message broker for background and asynchronous jobs"),
                     ("Swagger / OpenAPI", "Describing and documenting APIs")],
                ),
                role(
                    "Software Engineer",
                    "Software Engineers apply engineering principles across the full software life cycle: "
                    "requirements, design, construction, testing and maintenance. They write clean, well-tested code, "
                    "review others' work and help deliver dependable software as part of a team.",
                    ["Object-oriented programming and design", "Data structures and algorithms", "Requirements analysis and UML",
                     "Clean code and refactoring", "Unit testing and test-driven development", "Version control and code review",
                     "Agile and Scrum practices", "Debugging and profiling"],
                    ["Teamwork", "Communication", "Problem solving", "Time management", "Receiving and giving code review feedback"],
                    [("Jira", "Planning and tracking work in Agile teams"),
                     ("JUnit / pytest", "Writing automated unit tests"),
                     ("SonarQube", "Measuring code quality and finding code smells"),
                     ("Docker", "Running applications in consistent environments"),
                     ("PlantUML or draw.io", "Drawing UML and architecture diagrams")],
                ),
                role(
                    "Software Architect",
                    "Software Architects make the high-level design decisions for software systems. They choose "
                    "architectural styles and technologies, define how components communicate, balance quality "
                    "attributes such as scalability, security and cost, and guide teams in following the design. This "
                    "is usually a senior role reached after several years as a developer or software engineer.",
                    ["Architectural styles (layered, microservices, event-driven)", "Design patterns and SOLID principles",
                     "System design and scalability", "API and integration design", "Data architecture",
                     "Security architecture", "Cloud architecture", "Architecture documentation (C4 model, UML)"],
                    ["Leadership", "Decision-making", "Communicating with stakeholders", "Mentoring", "Strategic thinking"],
                    [("C4 model", "Documenting architecture at different levels of detail"),
                     ("Kubernetes", "Running and scaling microservices"),
                     ("Apache Kafka", "Event streaming between services"),
                     ("AWS / Azure Well-Architected Framework", "Best practices for reliable, secure and cost-efficient cloud systems"),
                     ("Architecture Decision Records", "Recording important design decisions and their reasons")],
                ),
            ],
        },
        {
            "name": "Software Quality Assurance & Testing",
            "description": (
                "Software Quality Assurance and Testing make sure software works correctly, meets its requirements "
                "and is reliable before it reaches users. The domain covers test planning, manual and automated "
                "testing, defect tracking, quality metrics and quality processes."
            ),
            "color": "#9333EA",
            "core": [
                "SEC 3608 Software Quality Engineering and Testing", "SEC 2407 Software Requirement Engineering",
                "SEC 3604 Software Construction and Development", "SEC 3603 Software Project Management",
                "CSC 4109 Professional Practices",
            ],
            "electives": [
                "SEC 4542 Software Metrics", "SEC 4531 Information Systems Audit", "SEC 4529 Global Software Development",
            ],
            "roles": [
                role(
                    "QA Engineer",
                    "QA Engineers check that software meets its requirements and quality standards. They review "
                    "requirements, write test plans and test cases, test features manually, report defects clearly and "
                    "confirm fixes before each release.",
                    ["Software testing life cycle", "Test case and test plan design", "Black-box testing techniques",
                     "Functional and regression testing", "Defect reporting and tracking", "API testing basics",
                     "SQL for data checks", "Agile testing practices"],
                    ["Attention to detail", "Clear written communication", "Critical thinking", "Patience", "Collaboration with developers"],
                    [("Jira", "Logging and tracking defects"),
                     ("TestRail", "Managing test cases and test runs"),
                     ("Postman", "Testing APIs manually and with scripts"),
                     ("ISTQB Foundation Level", "Internationally recognised software testing certification"),
                     ("BrowserStack", "Testing on many real browsers and devices")],
                ),
                role(
                    "Software Test Engineer",
                    "Software Test Engineers design and run tests at different levels, from individual units to whole "
                    "systems. They analyse risks, measure test coverage, test performance and security basics, and "
                    "report on the quality of each release.",
                    ["Test levels (unit, integration, system, acceptance)", "White-box and black-box techniques",
                     "Test coverage analysis", "Performance testing basics", "API testing", "Test data management",
                     "Programming in Java or Python", "Version control"],
                    ["Analytical thinking", "Documentation", "Communication", "Persistence", "Teamwork"],
                    [("JUnit / pytest", "Unit and integration test frameworks"),
                     ("Apache JMeter", "Load and performance testing"),
                     ("OWASP ZAP", "Basic security testing of web applications"),
                     ("Postman / Newman", "Automating API test collections"),
                     ("JaCoCo / Coverage.py", "Measuring code coverage of tests")],
                ),
                role(
                    "Automation Test Engineer / SDET",
                    "Automation Test Engineers, also called Software Development Engineers in Test (SDETs), write code "
                    "that tests software automatically. They build and maintain test frameworks, automate UI and API "
                    "tests, and run them in CI/CD pipelines so every change is checked quickly.",
                    ["Programming in Java, Python or JavaScript", "UI test automation", "API test automation",
                     "Test framework design (Page Object Model)", "Behaviour-driven development", "CI/CD integration",
                     "Git version control", "Debugging flaky tests"],
                    ["Problem solving", "Attention to detail", "Collaboration with developers", "Continuous learning", "Ownership of quality"],
                    [("Selenium WebDriver", "Automating browser-based UI tests"),
                     ("Playwright / Cypress", "Modern, fast end-to-end web test automation"),
                     ("Appium", "Automating tests for mobile apps"),
                     ("Cucumber", "Writing behaviour-driven tests in plain language"),
                     ("Jenkins / GitHub Actions", "Running automated test suites on every code change")],
                ),
            ],
        },
        {
            "name": "Mobile App Development",
            "description": (
                "Mobile App Development focuses on engineering applications for smartphones and tablets. The domain "
                "covers native and cross-platform development, mobile user experience, app architecture, testing and "
                "publishing apps to app stores."
            ),
            "color": "#EA580C",
            "core": [
                "CSC 1208 Object Oriented Programming Techniques", "SEC 2406 Software Design and Architecture",
                "SEC 3604 Software Construction and Development", "CSC 2203 Database Systems",
            ],
            "electives": [
                "SEC 3612 Mobile Application Development", "SEC 4549 User Interface Design", "SEC 4518 Visual Programming",
                "SEC 4547 Virtual and Augmented Reality", "SEC 4535 Multimedia Communication",
            ],
            "roles": [
                role(
                    "Android Developer",
                    "Android Developers build native Android applications. They design screens and navigation, use "
                    "device features, store data locally, connect to APIs and publish and update apps on the Google "
                    "Play Store.",
                    ["Kotlin", "Android SDK and Android Studio", "Jetpack Compose", "MVVM architecture",
                     "Room / SQLite local storage", "REST API integration", "App lifecycle and background work",
                     "Testing and debugging"],
                    ["User empathy", "Attention to detail", "Problem solving", "Teamwork", "Adaptability"],
                    [("Retrofit", "Calling REST APIs from Android apps"),
                     ("Firebase", "Authentication, database, analytics and push notifications"),
                     ("Hilt", "Dependency injection for maintainable Android code"),
                     ("Google Play Console", "Publishing and monitoring Android apps"),
                     ("Espresso", "Automated UI testing on Android")],
                ),
                role(
                    "Cross-Platform Mobile Developer",
                    "Cross-Platform Mobile Developers build apps for Android and iOS from a single codebase. They "
                    "create shared interfaces and logic, use plugins for device features and handle builds and releases "
                    "for both platforms.",
                    ["Flutter (Dart) or React Native (JavaScript/TypeScript)", "State management", "Responsive layouts",
                     "REST API integration", "Local storage", "Platform channels and native modules",
                     "App store release process", "Git version control"],
                    ["Adaptability", "Communication", "Time management", "Problem solving", "User-centred thinking"],
                    [("Flutter", "Building Android and iOS apps from one Dart codebase"),
                     ("React Native", "Building native mobile apps with JavaScript and React"),
                     ("Expo", "Faster React Native development, testing and builds"),
                     ("Firebase", "Backend services for mobile apps"),
                     ("Fastlane", "Automating app builds, signing and store releases")],
                ),
                role(
                    "Mobile Application Engineer",
                    "Mobile Application Engineers apply software engineering practices to mobile apps. They design app "
                    "architecture, write maintainable and tested code, optimise performance, battery and memory use, and "
                    "set up automated builds so apps stay reliable as they grow.",
                    ["Mobile app architecture (MVVM, Clean Architecture)", "Kotlin, Swift or Dart", "Unit and UI testing for mobile",
                     "Performance and memory optimisation", "Offline storage and data synchronisation", "Mobile security basics",
                     "CI/CD for mobile apps", "Crash and analytics monitoring"],
                    ["Engineering discipline", "Ownership", "Collaboration", "Analytical thinking", "Mentoring"],
                    [("Firebase Crashlytics", "Tracking and fixing app crashes in production"),
                     ("Bitrise / Codemagic", "CI/CD services built for mobile apps"),
                     ("Android Profiler / Xcode Instruments", "Finding performance and memory problems"),
                     ("SQLDelight / Room", "Type-safe local databases for mobile apps"),
                     ("Detox / Appium", "End-to-end testing of mobile apps")],
                ),
            ],
        },
        {
            "name": "Cloud Computing & DevOps",
            "description": (
                "Cloud Computing and DevOps focus on delivering and running software reliably. The domain covers "
                "cloud infrastructure, automated build and deployment pipelines, containers, monitoring and the "
                "collaboration between development and operations teams."
            ),
            "color": "#DB2777",
            "core": [
                "CSC 3107 Operating Systems", "CSC 3209 Computer Networks", "CSC 4106 Parallel and Distributed Computing",
                "CSC 4107 Information Security", "SEC 3604 Software Construction and Development",
            ],
            "electives": [
                "SEC 4532 Introduction to Cloud Computing", "SEC 4548 Introduction to Development Operations",
                "SEC 4525 Data Encryption and Security", "SEC 4543 Systems Programming",
            ],
            "roles": [
                role(
                    "Cloud Engineer",
                    "Cloud Engineers build and manage infrastructure on cloud platforms. They provision compute, "
                    "networking, storage and databases, manage access and costs, and keep cloud-hosted applications "
                    "secure and available.",
                    ["AWS, Azure or Google Cloud fundamentals", "Linux administration", "Cloud networking and security groups",
                     "Identity and access management", "Managed databases and storage", "Infrastructure as code",
                     "Scripting in Bash or Python", "Backup and disaster recovery"],
                    ["Planning", "Problem solving", "Documentation", "Security awareness", "Collaboration"],
                    [("Terraform", "Provisioning cloud infrastructure as code"),
                     ("AWS Certified Cloud Practitioner", "Entry-level AWS certification"),
                     ("Azure Fundamentals (AZ-900)", "Entry-level Microsoft Azure certification"),
                     ("Docker", "Containerising applications for the cloud"),
                     ("CloudWatch / Azure Monitor", "Monitoring cloud resources and alerts")],
                ),
                role(
                    "DevOps Engineer",
                    "DevOps Engineers automate the path from code to production. They build CI/CD pipelines, manage "
                    "containers and infrastructure as code, and add monitoring so teams can release software frequently "
                    "and safely.",
                    ["Linux and shell scripting", "Git workflows", "CI/CD pipelines", "Docker", "Kubernetes basics",
                     "Infrastructure as code", "Monitoring and logging", "Networking fundamentals"],
                    ["Cross-team collaboration", "Automation mindset", "Troubleshooting", "Continuous learning", "Communication"],
                    [("GitHub Actions / GitLab CI", "Automating build, test and deploy pipelines"),
                     ("Kubernetes", "Orchestrating containers in production"),
                     ("Ansible", "Automating server configuration"),
                     ("Helm", "Packaging and deploying Kubernetes applications"),
                     ("Prometheus and Grafana", "Collecting and visualising metrics")],
                ),
                role(
                    "Site Reliability Engineer",
                    "Site Reliability Engineers keep production services reliable and fast. They set reliability "
                    "targets, build observability, automate operational work, handle incidents and run post-incident "
                    "reviews to stop problems recurring.",
                    ["Linux internals", "Programming in Python or Go", "Observability (metrics, logs, traces)",
                     "SLOs and error budgets", "Incident management", "Load balancing and caching",
                     "Distributed systems", "Capacity planning"],
                    ["Calm under pressure", "Analytical thinking", "Blameless communication", "Ownership", "Documentation"],
                    [("Prometheus and Alertmanager", "Metrics collection and alerting"),
                     ("Grafana", "Reliability dashboards"),
                     ("OpenTelemetry", "Standard collection of traces, metrics and logs"),
                     ("PagerDuty", "On-call scheduling and incident escalation"),
                     ("k6", "Load testing services before traffic peaks")],
                ),
            ],
        },
        {
            "name": "Data Science & Intelligent Applications",
            "description": (
                "Data Science and Intelligent Applications focus on using data and artificial intelligence inside "
                "software products. The domain covers analysing data, building predictive models and engineering "
                "applications with intelligent features such as recommendations, language understanding and computer "
                "vision."
            ),
            "color": "#DC2626",
            "core": [
                "CSC 3206 Artificial Intelligence", "CSC 1206 Probability and Statistics", "CSC 2206 Linear Algebra",
                "CSC 2203 Database Systems",
            ],
            "electives": [
                "SEC 4514 Introduction to Data Science", "SEC 4522 Big Data Analytics", "SEC 4536 Natural Language Processing",
                "SEC 4524 Computer Vision", "SEC 4515 Digital Image Processing", "SEC 4521 Agent Based Software Engineering",
            ],
            "roles": [
                role(
                    "Data Analyst",
                    "Data Analysts gather, clean and analyse data to answer questions and track performance. They write "
                    "queries, build dashboards and reports, and present clear findings that help teams make decisions.",
                    ["SQL querying", "Microsoft Excel", "Descriptive statistics", "Data cleaning", "Data visualisation",
                     "Python with pandas", "Dashboard design", "KPI definition and tracking"],
                    ["Business understanding", "Storytelling with data", "Attention to detail", "Curiosity", "Presentation skills"],
                    [("Power BI", "Interactive dashboards and reports"),
                     ("Tableau", "Visual analytics and data exploration"),
                     ("Google Looker Studio", "Free web-based reporting tool"),
                     ("Jupyter Notebook", "Documenting analysis with code and charts"),
                     ("Git", "Versioning queries and notebooks")],
                ),
                role(
                    "Junior Data Scientist",
                    "Junior Data Scientists apply statistics and machine learning to find patterns and make "
                    "predictions. They explore data, build and validate models and explain results to technical and "
                    "business teams.",
                    ["Python (pandas, NumPy)", "Statistics and hypothesis testing", "Machine learning with scikit-learn",
                     "Exploratory data analysis", "Feature engineering", "SQL", "Data visualisation", "Model validation"],
                    ["Critical thinking", "Clear communication", "Curiosity", "Business awareness", "Teamwork"],
                    [("Kaggle", "Practising with real datasets and competitions"),
                     ("XGBoost / LightGBM", "Gradient boosting models for tabular data"),
                     ("Apache Spark (PySpark)", "Analysing large datasets in parallel"),
                     ("Plotly", "Interactive charts for presenting results"),
                     ("MLflow", "Tracking experiments and model versions")],
                ),
                role(
                    "AI Software Developer",
                    "AI Software Developers engineer software products with built-in intelligent features such as "
                    "chatbots, recommendations, document processing and image recognition. They integrate machine "
                    "learning models and AI APIs into applications, test their behaviour and deploy them reliably.",
                    ["Python programming", "Machine learning fundamentals", "Integrating AI and language-model APIs",
                     "Prompt engineering", "REST API development", "Natural language processing basics",
                     "Computer vision basics", "Testing and evaluating AI features"],
                    ["Problem solving", "Ethical judgement", "User focus", "Communication", "Continuous learning"],
                    [("Hugging Face Transformers", "Using pre-trained language and vision models"),
                     ("LangChain", "Building applications around language-model workflows"),
                     ("FastAPI", "Serving AI models through web APIs"),
                     ("Vector databases (e.g. pgvector)", "Semantic search and retrieval for AI applications"),
                     ("Docker", "Packaging AI services for deployment")],
                ),
            ],
        },
    ],
}

ROADMAPS = [BSCS, BSSE]


def role_sections(r):
    """The four detail sections of a job role, validated exactly as the roadmap editor API would."""
    raw = [
        {"section_title": "Job Description", "section_type": "text", "content": {"text": r["description"]}},
        {"section_title": "Technical Skills", "section_type": "skills", "content": {"items": r["technical"]}},
        {"section_title": "Soft Skills", "section_type": "list", "content": {"items": r["soft"]}},
        {"section_title": "Additional Technologies to Learn", "section_type": "list",
         "content": {"items": [f"{name}: {purpose}" for name, purpose in r["tools"]]}},
    ]
    return [RoadmapSectionIn.model_validate(section) for section in raw]


def check_data():
    """Fail before touching the database if anything breaks the expected structure or the API's rules."""
    for roadmap in ROADMAPS:
        assert len(roadmap["domains"]) == 6, roadmap["title"]
        assert len(roadmap["title"]) <= 200
        for domain in roadmap["domains"]:
            RoadmapBranchIn(name=domain["name"], color=domain["color"])
            assert len(domain["roles"]) == 3, domain["name"]
            for r in domain["roles"]:
                assert len(r["title"]) <= 150
                for section in role_sections(r):
                    items = section.content.get("items")
                    assert items is None or len(items) >= 3, (r["title"], section.section_title)


def seed(db):
    stats = {"roadmaps_inserted": 0, "roadmaps_updated": 0, "branches_inserted": 0, "branches_updated": 0,
             "nodes_inserted": 0, "nodes_updated": 0, "sections_inserted": 0, "sections_replaced": 0}
    for roadmap in ROADMAPS:
        program_id = db.execute(text("SELECT id FROM programs WHERE slug = :slug"), {"slug": roadmap["slug"]}).scalar()
        if program_id is None:
            raise RuntimeError(f"Program {roadmap['slug']} not found")
        linked = db.execute(text("SELECT id FROM roadmaps WHERE program_id = :p ORDER BY id"), {"p": program_id}).scalars().all()
        if len(linked) > 1:
            raise RuntimeError(f"Program {roadmap['slug']} has several roadmaps {linked}; resolve this before seeding")
        if linked:
            roadmap_id = linked[0]
            db.execute(text("UPDATE roadmaps SET title = :t, description = :d, updated_at = now() WHERE id = :id"),
                       {"t": roadmap["title"], "d": roadmap["description"], "id": roadmap_id})
            stats["roadmaps_updated"] += 1
        else:
            roadmap_id = db.execute(text(
                "INSERT INTO roadmaps (title, description, program_id, status) VALUES (:t, :d, :p, 'published') RETURNING id"
            ), {"t": roadmap["title"], "d": roadmap["description"], "p": program_id}).scalar()
            stats["roadmaps_inserted"] += 1

        for b_pos, domain in enumerate(roadmap["domains"]):
            existing = db.execute(text("SELECT id, description FROM roadmap_branches WHERE roadmap_id = :r AND name = :n"),
                                  {"r": roadmap_id, "n": domain["name"]}).all()
            if len(existing) > 1:
                raise RuntimeError(f"Duplicate branch '{domain['name']}' in roadmap {roadmap_id}")
            courses = courses_text(domain["core"], domain["electives"])
            if existing:
                branch_id, current = existing[0]
                intro = domain["description"]
                if intro is None:  # keep the text entered from the dashboard (without any earlier course list)
                    intro = (current or "").split("\n\nRelevant SZABIST courses")[0].strip()
                db.execute(text("UPDATE roadmap_branches SET description = :d, color = :c, position = :p, updated_at = now() WHERE id = :id"),
                           {"d": f"{intro}\n\n{courses}", "c": domain["color"], "p": b_pos, "id": branch_id})
                stats["branches_updated"] += 1
            else:
                branch_id = db.execute(text(
                    "INSERT INTO roadmap_branches (roadmap_id, name, description, color, position) VALUES (:r, :n, :d, :c, :p) RETURNING id"
                ), {"r": roadmap_id, "n": domain["name"], "d": f"{domain['description']}\n\n{courses}",
                    "c": domain["color"], "p": b_pos}).scalar()
                stats["branches_inserted"] += 1

            for n_pos, r in enumerate(domain["roles"]):
                nodes = db.execute(text("SELECT id FROM roadmap_nodes WHERE branch_id = :b AND title = :t"),
                                   {"b": branch_id, "t": r["title"]}).scalars().all()
                if len(nodes) > 1:
                    raise RuntimeError(f"Duplicate step '{r['title']}' in branch {branch_id}")
                if nodes:
                    node_id = nodes[0]
                    db.execute(text("UPDATE roadmap_nodes SET position = :p, updated_at = now() WHERE id = :id"),
                               {"p": n_pos, "id": node_id})
                    removed = db.execute(text("DELETE FROM roadmap_node_sections WHERE node_id = :n"), {"n": node_id}).rowcount
                    stats["nodes_updated"] += 1
                    stats["sections_replaced"] += removed
                else:
                    node_id = db.execute(text(
                        "INSERT INTO roadmap_nodes (branch_id, title, position) VALUES (:b, :t, :p) RETURNING id"
                    ), {"b": branch_id, "t": r["title"], "p": n_pos}).scalar()
                    stats["nodes_inserted"] += 1
                for s_pos, section in enumerate(role_sections(r)):
                    db.execute(text(
                        "INSERT INTO roadmap_node_sections (node_id, section_title, section_type, content, position) "
                        "VALUES (:n, :t, :ty, CAST(:c AS jsonb), :p)"
                    ), {"n": node_id, "t": section.section_title, "ty": section.section_type,
                        "c": json.dumps(section.content), "p": s_pos})
                    stats["sections_inserted"] += 1
    return stats


def main():
    check_data()
    db = SessionLocal()
    try:
        stats = seed(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
