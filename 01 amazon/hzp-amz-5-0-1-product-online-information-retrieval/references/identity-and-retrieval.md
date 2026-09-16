# Identity and retrieval reference

Product Code is the only user input. Resolve it to one Product Root and read `01_产品档案.md`. Marketplace and Current/Child ASIN must be explicitly present; Product Code is not an ASIN and the marketplace must not default to US. Reuse the repository's shared mapping/resolver when invoking the Skill.

The page URL is the mapped Amazon domain plus `/dp/{ASIN}`. Validate expected and retrieved ASIN, marketplace, brand, title and variant. On mismatch use `PRODUCT_IDENTITY_CONFLICT`. A blocked page may be retried through Amazon-only exact-ASIN routes. Third-party sites are not substitutes.
