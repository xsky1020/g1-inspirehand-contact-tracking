# GitHub Checklist

Recommended repository name:

```text
dreamcontrol-contact-eval
```

Before pushing:

```bash
git status --short
git lfs ls-files
```

Keep:

- `Sim2Real/deploy/deploy_mujoco/`
- `Sim2Real/deploy/policies/`
- `Sim2Real/resources/robots/g1_description/`
- root handoff/report markdown files

Do not commit generated runtime outputs:

```text
metrics/
logs/
outputs/
wandb/
__pycache__/
*.pyc
```

Push:

```bash
git remote add origin <github-url>
git push -u origin main
```

Note:

The repo includes model assets and `.pt` policies, so Git LFS is recommended.
