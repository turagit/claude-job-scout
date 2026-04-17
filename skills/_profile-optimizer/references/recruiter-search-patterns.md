# Recruiter Search Patterns

## How to Use This Reference

When optimising a LinkedIn profile, use these patterns to:
1. Choose job titles that match what recruiters type into search
2. Build Boolean queries to test whether the profile would surface
3. Ensure exact-match phrases appear in searchable fields

## Standard Job Title Mappings

Recruiters search for standard titles. If the user's CV has a creative or internal title, map it to the searchable equivalent for LinkedIn.

### Engineering
| Creative / Internal Title | Searchable LinkedIn Title |
|--------------------------|--------------------------|
| Code Ninja, Software Craftsman | Software Engineer |
| Full-Stack Wizard | Full Stack Developer |
| Engineering Lead, Tech Lead | Senior Software Engineer / Engineering Manager |
| Platform Hacker | Platform Engineer |
| Cloud Guy, Infrastructure Lead | Cloud Engineer / DevOps Engineer |
| Data Wrangler | Data Engineer |
| ML Wizard, AI Specialist | Machine Learning Engineer |
| SRE, Reliability Lead | Site Reliability Engineer |
| Scrum Master / Agile Coach | Agile Delivery Manager |

### Product & Design
| Creative / Internal Title | Searchable LinkedIn Title |
|--------------------------|--------------------------|
| Product Owner (when strategic) | Product Manager |
| UX Guru, Design Lead | UX Designer / Product Designer |
| Growth Hacker | Growth Product Manager |
| Design Technologist | UX Engineer |

### Data
| Creative / Internal Title | Searchable LinkedIn Title |
|--------------------------|--------------------------|
| Data Rockstar | Data Scientist |
| Analytics Lead | Data Analyst / Analytics Engineer |
| BI Specialist | Business Intelligence Analyst |
| Insights Manager | Data Analytics Manager |

### Management
| Creative / Internal Title | Searchable LinkedIn Title |
|--------------------------|--------------------------|
| Head of Engineering | VP of Engineering / Engineering Director |
| Team Lead | Engineering Manager |
| CTO (at startup <20 people) | CTO / Senior Software Engineer |
| Delivery Lead | Technical Program Manager |

**Rule:** Use the searchable title as the primary LinkedIn title. If the actual title is different, include both: `Senior Software Engineer / Tech Lead at [Company]`

## Common Boolean Queries by Role

Use these to test profile discoverability. The user's profile should contain all required keywords.

### Software Engineer
```
"software engineer" AND ("Java" OR "Python" OR "Go") AND ("AWS" OR "GCP" OR "Azure")
"senior software engineer" AND "microservices" AND ("Kubernetes" OR "Docker")
"backend engineer" AND "API" AND ("Node.js" OR "Python" OR "Java")
```

### Frontend Developer
```
"frontend" AND ("React" OR "Vue" OR "Angular") AND ("TypeScript" OR "JavaScript")
"frontend developer" AND "responsive" AND ("CSS" OR "Tailwind" OR "styled-components")
```

### Data Engineer
```
"data engineer" AND ("Spark" OR "PySpark") AND ("AWS" OR "GCP" OR "Azure")
"data engineer" AND ("Airflow" OR "dbt") AND ("SQL" OR "Python")
"data platform" AND ("Kafka" OR "streaming") AND "pipeline"
```

### DevOps / Platform
```
"DevOps" AND ("Terraform" OR "CloudFormation") AND ("CI/CD" OR "Jenkins" OR "GitHub Actions")
"platform engineer" AND "Kubernetes" AND ("AWS" OR "GCP")
"SRE" AND ("monitoring" OR "observability") AND ("Prometheus" OR "Datadog" OR "Grafana")
```

### Product Manager
```
"product manager" AND ("B2B" OR "B2C" OR "SaaS") AND "roadmap"
"product manager" AND ("data-driven" OR "analytics") AND "stakeholder"
"senior product manager" AND "strategy" AND ("OKR" OR "KPI")
```

### Data Scientist / ML
```
"data scientist" AND ("Python" OR "R") AND ("machine learning" OR "ML")
"machine learning engineer" AND ("TensorFlow" OR "PyTorch") AND "production"
"NLP" AND ("LLM" OR "transformer") AND ("Python" OR "deep learning")
```

## Recruiter Filter Priorities

What recruiters filter on first (in order of typical usage):

1. **Keywords** (in headline + title + skills) — this is the primary filter
2. **Location** — city, region, or "remote" — must match user's target
3. **Open to Work** — many recruiters filter for this exclusively
4. **Current title** — used as a proxy for seniority and relevance
5. **Years of experience** — derived from profile dates
6. **Skills** — used as secondary filter to narrow results
7. **Industry** — occasionally used for domain-specific roles

## Keyword Exact-Match Importance

Recruiters type exact phrases. The profile must contain these exact strings, not synonyms:

| Recruiter searches for | Won't match |
|----------------------|-------------|
| "CI/CD" | "Continuous Integration and Continuous Deployment" |
| "React" | "React.js framework" (as a skill entry) |
| "AWS" | "Amazon Web Services" (add both forms) |
| "Kubernetes" | "K8s" (add both forms) |
| "Machine Learning" | "ML" (add both forms) |
| "Product Manager" | "PM" or "Product Owner" |

**Rule:** Include both the acronym and the spelled-out form in different profile sections to cover all search variations.
