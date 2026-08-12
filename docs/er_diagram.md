# CivicConnect ER Diagram

```mermaid
erDiagram
    USERS ||--o{ ISSUES : submits

    USERS {
        int id PK
        string name
        string email
        string password
    }

    ISSUES {
        int id PK
        string category
        string location
        string description
        string image
        string status
    }
```
