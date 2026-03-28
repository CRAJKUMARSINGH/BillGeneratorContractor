# Technical Documentation

**For Developers and Advanced Users**

This directory contains detailed technical documentation about the system's internals, known limitations, and improvement plans.

---

## 📚 Contents

### [Known Issues and Limitations](KNOWN_ISSUES_AND_LIMITATIONS.md)
Detailed documentation of edge cases, failure scenarios, and technical limitations. This is primarily for developers who need to understand the system's behavior in various scenarios.

### [Production Improvements Plan](PRODUCTION_IMPROVEMENTS_PLAN.md)
Roadmap for future reliability improvements, including technical implementation details and success metrics.

---

## 👥 Audience

This documentation is intended for:
- **Developers** contributing to the project
- **System administrators** deploying the application
- **Technical support** staff troubleshooting issues
- **Advanced users** who want to understand the internals

---

## 📖 User Documentation

If you're a regular user looking for help, see:
- [User Manual](../../USER_MANUAL.md) - Complete guide for contractors
- [Reliability Guide](../../RELIABILITY.md) - Production-ready features
- [Quick Start](../../README.md#-quick-start) - Getting started
- [Video Tutorials](../../VIDEO_GUIDE_SCRIPT.md) - Step-by-step videos

---

## 🔧 Developer Resources

### Contributing
See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on:
- Code style and standards
- Testing requirements
- Pull request process
- Development setup

### Architecture
- Core modules in `core/` directory
- Processors in `core/processors/`
- Generators in `core/generators/`
- Utilities in `core/utils/`

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test
pytest tests/test_extraction.py
```

---

## 🐛 Reporting Issues

Found a bug? Please report it:
1. Check [Known Issues](KNOWN_ISSUES_AND_LIMITATIONS.md) first
2. Search [GitHub Issues](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor/issues)
3. If not found, [create a new issue](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor/issues/new)

Include:
- System information (OS, Python version)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs from `logs/` directory

---

## 💡 Feature Requests

Have an idea for improvement?
1. Check [Production Improvements Plan](PRODUCTION_IMPROVEMENTS_PLAN.md)
2. Search [GitHub Discussions](https://github.com/CRAJKUMARSINGH/BillGeneratorContractor/discussions)
3. Create a new discussion with your proposal

---

## 📞 Contact

For technical questions:
- **GitHub Issues:** Bug reports and technical problems
- **GitHub Discussions:** Feature requests and questions
- **Email:** crajkumarsingh@hotmail.com

---

**Note:** This technical documentation is maintained separately from user-facing documentation to keep the main README focused on features and benefits rather than technical details.
