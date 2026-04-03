# Ponder Backend

## Environment Setup

### Managing Environment Variables
We use separate environment files for development and production:

1. Development Setup:
   ```bash
   cp .env.development .env
   ```

2. Production Setup:
   ```bash
   cp .env.production .env
   ```

Key differences:
- Development: Local URLs, debug logging, shorter retention
- Production: Secure remote URLs, info logging, longer retention

Never commit `.env` or `.env.production` files. Only `.env.development` and `.env.example` should be in version control.

### Production
1. Data Management:
   - Backups are stored in `DATABASE_BACKUP_DIR`
   - Analytics exports go to `ANALYTICS_EXPORT_DIR`
   - Old data is automatically cleaned up based on retention settings

2. Admin API Endpoints:
   - All endpoints require `X-Admin-Key` header
   - `/api/v1/admin/stats` - System statistics
   - `/api/v1/admin/backup` - Create backup
   - `/api/v1/admin/cleanup` - Clean old data
   - `/api/v1/admin/export-analytics` - Export analytics

3. Monitoring:
   - Check logs in specified log directory
   - Monitor system stats via admin API
   - Set up alerts for backup failures
   - Track database size and performance

### Security Notes
- Never commit `.env` file
- Change all default keys in production
- Use strong, unique keys for admin API
- Store backups in secure location
- Monitor admin API access

### Maintenance
- Regular backups are automatic
- Old data cleanup runs on schedule
- Analytics exports can be automated
- Monitor system stats regularly
