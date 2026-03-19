-- Table name catalog
DROP TABLE IF EXISTS project_table_catalog;
CREATE TABLE project_table_catalog (
  id INT NOT NULL AUTO_INCREMENT,
  table_name VARCHAR(128) NOT NULL,
  export_order INT NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_table_name (table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO project_table_catalog (table_name, export_order) VALUES ('user', 1);
INSERT INTO project_table_catalog (table_name, export_order) VALUES ('role_permission', 2);
INSERT INTO project_table_catalog (table_name, export_order) VALUES ('knowledge_chunk', 3);
INSERT INTO project_table_catalog (table_name, export_order) VALUES ('prediction_record', 4);
INSERT INTO project_table_catalog (table_name, export_order) VALUES ('disease_case', 5);
INSERT INTO project_table_catalog (table_name, export_order) VALUES ('followup_plan', 6);
INSERT INTO project_table_catalog (table_name, export_order) VALUES ('followup_checkin', 7);
INSERT INTO project_table_catalog (table_name, export_order) VALUES ('region_alert', 8);
