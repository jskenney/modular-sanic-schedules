###############################################################################
## Default MySQL tables for course schedule purposes within the framework

DROP TABLE IF EXISTS sched_semester;
DROP TABLE IF EXISTS sched_section_instructors;
DROP TABLE IF EXISTS sched_section;
DROP TABLE IF EXISTS sched_instructor;
DROP TABLE IF EXISTS sched_student;
DROP TABLE IF EXISTS sched_course;
DROP TABLE IF EXISTS sched_current;

CREATE TABLE `sched_current` (
  `school` VARCHAR(32) NOT NULL,
  `year` VARCHAR(8) NOT NULL,
  `semester` VARCHAR(16) NOT NULL,
  `block` VARCHAR(8) DEFAULT "1",
  CONSTRAINT PK_sched_current PRIMARY KEY (school)
);

CREATE TABLE `sched_course` (
  `school` VARCHAR(32) NOT NULL,
  `course` VARCHAR(16) NOT NULL,
  `title`  VARCHAR(128) NULL,
  `department` VARCHAR(128) NULL,
  CONSTRAINT PK_sched_course PRIMARY KEY (school, course)
);

CREATE TABLE `sched_student` (
  `school` VARCHAR(32) NOT NULL,
  `student` VARCHAR(32) NOT NULL,
  `name` VARCHAR(128) NULL,
  CONSTRAINT PK_sched_student PRIMARY KEY (school, student)
);

CREATE TABLE `sched_instructor` (
  `school` VARCHAR(32) NOT NULL,
  `instructor` VARCHAR(32) NOT NULL,
  `name` VARCHAR(128) NULL,
  `department` VARCHAR(128) NULL,
  CONSTRAINT PK_sched_instructor PRIMARY KEY (school, instructor)
);

CREATE TABLE `sched_section` (
  `school` VARCHAR(32) NOT NULL,
  `course` VARCHAR(16) NOT NULL,
  `section` VARCHAR(8) NOT NULL,
  `location` VARCHAR(64) NULL,
  `time` VARCHAR(64) NULL,
  CONSTRAINT PK_sched_section PRIMARY KEY (school, course, section)
);

CREATE TABLE `sched_section_instructors` (
  `school` VARCHAR(32) NOT NULL,
  `section` VARCHAR(8) NOT NULL,
  `course` VARCHAR(16) NOT NULL,
  `instructor` VARCHAR(32) NOT NULL,
  `pri` BOOLEAN DEFAULT 0,
  CONSTRAINT PK_sched_section_inst PRIMARY KEY (school, course, section, instructor)
);

CREATE TABLE `sched_semester` (
  `school`   VARCHAR(32) NOT NULL,
  `course`   VARCHAR(16) NOT NULL,
  `section`  VARCHAR(8) NOT NULL,
  `student`  VARCHAR(32) NOT NULL,
  CONSTRAINT PK_sched_semester PRIMARY KEY (school, course, section, student)
);
