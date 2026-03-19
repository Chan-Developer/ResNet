-- Auto-generated schema export
-- Database: plant_disease
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for `user`
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `hashed_password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'user',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for `role_permission`
-- ----------------------------
DROP TABLE IF EXISTS `role_permission`;
CREATE TABLE `role_permission` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `permissions_json` varchar(2000) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `role` (`role`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for `knowledge_chunk`
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_chunk`;
CREATE TABLE `knowledge_chunk` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `label_key` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `crop_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `disease_family` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `health_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_name` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tags_json` json NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `idx_knowledge_crop` (`crop_name`),
  KEY `idx_knowledge_label` (`label_key`),
  KEY `idx_knowledge_family` (`disease_family`)
) ENGINE=InnoDB AUTO_INCREMENT=91 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for `prediction_record`
-- ----------------------------
DROP TABLE IF EXISTS `prediction_record`;
CREATE TABLE `prediction_record` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `image_filename` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `top1_class` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `top1_confidence` float NOT NULL,
  `top_k` smallint NOT NULL,
  `results_json` json NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_prediction_record_user_id` (`user_id`),
  KEY `idx_user_created` (`user_id`,`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for `disease_case`
-- ----------------------------
DROP TABLE IF EXISTS `disease_case`;
CREATE TABLE `disease_case` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `prediction_record_id` bigint NOT NULL,
  `image_filename` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `predicted_label` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `confirmed_label` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `crop_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `disease_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `health_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `confidence` float NOT NULL,
  `status` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `diagnostic_summary` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `advice_json` json NOT NULL,
  `evidence_json` json NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `province` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `region_code` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '未知区域',
  `lat` double DEFAULT NULL,
  `lng` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_disease_case_user_id` (`user_id`),
  KEY `idx_case_user_created` (`user_id`,`created_at`),
  KEY `ix_disease_case_prediction_record_id` (`prediction_record_id`),
  KEY `idx_case_label_created` (`confirmed_label`,`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for `followup_plan`
-- ----------------------------
DROP TABLE IF EXISTS `followup_plan`;
CREATE TABLE `followup_plan` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `case_id` bigint DEFAULT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_label` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `frequency_days` int NOT NULL,
  `start_date` date NOT NULL,
  `next_review_date` date NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `latest_effect` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `effect_score` float DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `idx_followup_plan_user_status_next` (`user_id`,`status`,`next_review_date`),
  KEY `ix_followup_plan_case_id` (`case_id`),
  KEY `idx_followup_plan_case` (`case_id`),
  KEY `ix_followup_plan_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for `followup_checkin`
-- ----------------------------
DROP TABLE IF EXISTS `followup_checkin`;
CREATE TABLE `followup_checkin` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `plan_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `image_filename` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `top1_label` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `top1_confidence` float NOT NULL,
  `target_confidence` float NOT NULL,
  `target_confidence_delta` float NOT NULL,
  `top1_confidence_delta` float NOT NULL,
  `effect_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `effect_score` float NOT NULL,
  `llm_summary` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `note` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `results_json` json NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `idx_followup_checkin_plan_created` (`plan_id`,`created_at`),
  KEY `ix_followup_checkin_plan_id` (`plan_id`),
  KEY `ix_followup_checkin_user_id` (`user_id`),
  KEY `idx_followup_checkin_user_created` (`user_id`,`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for `region_alert`
-- ----------------------------
DROP TABLE IF EXISTS `region_alert`;
CREATE TABLE `region_alert` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `region_code` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `province` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `confirmed_label` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `current_count` int NOT NULL,
  `previous_count` int NOT NULL,
  `growth_rate` float NOT NULL,
  `threshold` float NOT NULL,
  `window_days` int NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `message` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `idx_alert_status_created` (`status`,`created_at`),
  KEY `idx_alert_region_label_created` (`region_code`,`confirmed_label`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
