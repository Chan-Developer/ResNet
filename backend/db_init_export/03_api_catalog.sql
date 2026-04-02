-- API endpoint catalog
DROP TABLE IF EXISTS project_api_catalog;
CREATE TABLE project_api_catalog (
  id INT NOT NULL AUTO_INCREMENT,
  method VARCHAR(16) NOT NULL,
  path VARCHAR(255) NOT NULL,
  permission_code VARCHAR(255) NULL,
  related_tables VARCHAR(255) NULL,
  note VARCHAR(500) NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/admin/permissions', 'admin:role', 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/admin/roles', 'admin:role', 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('PATCH', '/api/admin/roles/{role}/permissions', 'admin:role', 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/admin/users', 'admin:user', 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('PATCH', '/api/admin/users/{user_id}', 'admin:user', 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/alerts/region', 'admin:alert', 'region_alert,disease_case', '区域预警流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/alerts/region/summary', 'admin:alert', 'region_alert,disease_case', '区域预警流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('PATCH', '/api/alerts/region/{alert_id}/read', 'admin:alert', 'region_alert,disease_case', '区域预警流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('POST', '/api/auth/login', NULL, 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/auth/me', NULL, 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('POST', '/api/auth/register', NULL, 'user,role_permission', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('POST', '/api/case/confirm', 'diagnosis:confirm', 'prediction_record,disease_case,knowledge_chunk,region_alert', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/case/{case_id}', 'history:view', 'prediction_record,disease_case,knowledge_chunk,region_alert', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/case/{case_id}/similar', 'history:view', 'prediction_record,disease_case,knowledge_chunk,region_alert', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/dataset/categories', 'dataset:view', 'knowledge_chunk', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/dataset/categories/{name}/images', 'dataset:view', 'knowledge_chunk', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/followup/plans', 'followup:manage', 'followup_plan,followup_checkin,disease_case', '复查计划与复查记录流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('POST', '/api/followup/plans', 'followup:manage', 'followup_plan,followup_checkin,disease_case', '复查计划与复查记录流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/followup/plans/{plan_id}', 'followup:manage', 'followup_plan,followup_checkin,disease_case', '复查计划与复查记录流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('PATCH', '/api/followup/plans/{plan_id}', 'followup:manage', 'followup_plan,followup_checkin,disease_case', '复查计划与复查记录流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/followup/plans/{plan_id}/checkins', 'followup:manage', 'followup_plan,followup_checkin,disease_case', '复查计划与复查记录流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('POST', '/api/followup/plans/{plan_id}/checkins', 'followup:manage', 'followup_plan,followup_checkin,disease_case', '复查计划与复查记录流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/followup/plans/{plan_id}/evaluation', 'followup:manage', 'followup_plan,followup_checkin,disease_case', '复查计划与复查记录流程');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/health', NULL, NULL, NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/history', 'history:view', 'prediction_record,disease_case', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('DELETE', '/api/history/{record_id}', 'history:delete', 'prediction_record,disease_case', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('POST', '/api/predict', 'predict:single', 'prediction_record,knowledge_chunk', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('POST', '/api/predict/diagnose', 'predict:single', 'prediction_record,knowledge_chunk', NULL);
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/report/export.csv', NULL, 'prediction_record,disease_case', '统计看板与报表导出');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/report/export.xlsx', NULL, 'prediction_record,disease_case', '统计看板与报表导出');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/report/filters', NULL, 'prediction_record,disease_case', '统计看板与报表导出');
INSERT INTO project_api_catalog (method, path, permission_code, related_tables, note) VALUES ('GET', '/api/report/overview', NULL, 'prediction_record,disease_case', '统计看板与报表导出');
