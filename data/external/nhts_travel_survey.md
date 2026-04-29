# National Household Travel Survey

Source: https://nhts.ornl.gov/

The National Household Travel Survey is recommended as an extension dataset for travel behavior analysis.

## Suitable Questions

- Does household income affect car use?
- How do trip purpose and weekend status affect travel distance?
- Which factors are associated with choosing driving, transit, walking, or biking?
- How do household size and vehicle ownership affect trip frequency?

## Suggested Modeling Tasks

- Logistic regression: whether a trip is made by car.
- Poisson or negative binomial regression: number of trips per household or person.
- Zero-inflated count model: trip counts for rare modes such as biking or transit in some regions.

## Notes

The full NHTS public-use files can be large. For teaching, download a selected public-use file and create a smaller sample before committing it to this repository.
