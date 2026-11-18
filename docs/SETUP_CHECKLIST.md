# Setup checklist

- [ ] Create GitHub repository and upload project files
- [ ] Enable Actions and Pages (GitHub Actions deployment)
- [ ] Run the weekly discovery workflow manually
- [ ] Run the Pages workflow manually and open the published URL
- [ ] Configure SMTP secrets if weekly email is desired
- [ ] Add real, permitted RSS feeds to `config/sources.json`
- [ ] Add real scholarship listings using `python -m app.cli add`
- [ ] Verify all eligibility, deadlines and allowed funding uses
- [ ] Export dashboard statuses regularly
- [ ] Keep sensitive records and real application answers outside public repository

## Troubleshooting

**No scholarships appear:** Default source list contains directory bookmarks, not individual awards. Add verified individual award URLs or an active RSS feed.

**No emails:** Confirm SMTP secrets, provider SMTP support, host/port, and the workflow logs. The system intentionally skips email when secrets are absent.

**Dashboard not updating:** Verify Pages source is GitHub Actions, inspect the Pages workflow, and confirm the branch is `main`.

**Workflow cannot push:** Check Actions workflow permissions and branch protection rules.

**Personal notes missing:** Notes are local to one browser; import a previously exported backup.
