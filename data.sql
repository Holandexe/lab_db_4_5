-- =====================================================================
-- Лабораторна робота №3. Варіант 14: tickets.ua
-- Квитки на події (концерти, вистави), артисти, місця, замовлення,
-- опції доставки, оплата, квитки на поїзд/літак/автобус.
-- Скрипт можна запускати багато разів поспіль.
-- =====================================================================

-- Видаляємо стару версію БД (разом з будь-якими «чужими» таблицями,
-- що посилаються на наші), щоб скрипт завжди відпрацьовував чисто.
DROP DATABASE IF EXISTS tickets_ua;
CREATE DATABASE IF NOT EXISTS tickets_ua
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE tickets_ua;

SET NAMES utf8mb4;

-- ---------------------------------------------------------------------
-- DROP (у порядку, зворотному до залежностей)
-- ---------------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS transport_ticket;
DROP TABLE IF EXISTS ticket;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS transport_route;
DROP TABLE IF EXISTS event_seat;
DROP TABLE IF EXISTS seat;
DROP TABLE IF EXISTS event_artist;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS artist;
DROP TABLE IF EXISTS venue;
DROP TABLE IF EXISTS city;
DROP TABLE IF EXISTS country;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS delivery_option;
DROP TABLE IF EXISTS payment_method;
DROP TABLE IF EXISTS event_type;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- CREATE TABLE
-- ---------------------------------------------------------------------
CREATE TABLE country (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(60) NOT NULL,
    iso_code  CHAR(2)     NOT NULL,
    CONSTRAINT UQ_country_name UNIQUE (name),
    CONSTRAINT UQ_country_iso  UNIQUE (iso_code)
) ENGINE = INNODB;

CREATE TABLE city (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    country_id  INT         NOT NULL,
    name        VARCHAR(60) NOT NULL,
    CONSTRAINT UQ_city_country_name UNIQUE (country_id, name),
    CONSTRAINT FK_city_country FOREIGN KEY (country_id) REFERENCES country (id)
) ENGINE = INNODB;

CREATE TABLE venue (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    city_id   INT          NOT NULL,
    name      VARCHAR(100) NOT NULL,
    address   VARCHAR(150) NOT NULL,
    capacity  INT          NOT NULL,
    CONSTRAINT CHK_venue_capacity CHECK (capacity > 0),
    CONSTRAINT FK_venue_city FOREIGN KEY (city_id) REFERENCES city (id)
) ENGINE = INNODB;

CREATE TABLE event_type (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(50) NOT NULL,
    CONSTRAINT UQ_event_type_name UNIQUE (name)
) ENGINE = INNODB;

CREATE TABLE artist (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    country_id  INT          NOT NULL,
    name        VARCHAR(100) NOT NULL,
    genre       VARCHAR(50)  NOT NULL,
    bio         TEXT NULL,
    CONSTRAINT UQ_artist_name UNIQUE (name),
    CONSTRAINT FK_artist_country FOREIGN KEY (country_id) REFERENCES country (id)
) ENGINE = INNODB;

CREATE TABLE event (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    event_type_id   INT          NOT NULL,
    venue_id        INT          NOT NULL,
    title           VARCHAR(150) NOT NULL,
    description     TEXT NULL,
    start_datetime  DATETIME     NOT NULL,
    status          ENUM('scheduled','sold_out','cancelled','finished') NOT NULL DEFAULT 'scheduled',
    CONSTRAINT FK_event_type  FOREIGN KEY (event_type_id) REFERENCES event_type (id),
    CONSTRAINT FK_event_venue FOREIGN KEY (venue_id)      REFERENCES venue (id)
) ENGINE = INNODB;

-- зв'язок багато-до-багатьох: на події може виступати декілька артистів
CREATE TABLE event_artist (
    event_id   INT NOT NULL,
    artist_id  INT NOT NULL,
    PRIMARY KEY (event_id, artist_id),
    CONSTRAINT FK_event_artist_event  FOREIGN KEY (event_id)  REFERENCES event (id),
    CONSTRAINT FK_event_artist_artist FOREIGN KEY (artist_id) REFERENCES artist (id)
) ENGINE = INNODB;

CREATE TABLE seat (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    venue_id  INT         NOT NULL,
    sector    VARCHAR(30) NOT NULL,
    row_no    INT         NOT NULL,
    seat_no   INT         NOT NULL,
    CONSTRAINT UQ_seat_position UNIQUE (venue_id, sector, row_no, seat_no),
    CONSTRAINT FK_seat_venue FOREIGN KEY (venue_id) REFERENCES venue (id)
) ENGINE = INNODB;

-- наявність вільних місць на конкретну подію + ціна
CREATE TABLE event_seat (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    event_id  INT           NOT NULL,
    seat_id   INT           NOT NULL,
    price     DECIMAL(10,2) NOT NULL,
    status    ENUM('available','reserved','sold') NOT NULL DEFAULT 'available',
    CONSTRAINT UQ_event_seat UNIQUE (event_id, seat_id),
    CONSTRAINT CHK_event_seat_price CHECK (price >= 0),
    CONSTRAINT FK_event_seat_event FOREIGN KEY (event_id) REFERENCES event (id),
    CONSTRAINT FK_event_seat_seat  FOREIGN KEY (seat_id)  REFERENCES seat (id)
) ENGINE = INNODB;

CREATE TABLE customer (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    first_name     VARCHAR(50)  NOT NULL,
    last_name      VARCHAR(50)  NOT NULL,
    email          VARCHAR(100) NOT NULL,
    phone          VARCHAR(20)  NULL,
    registered_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT UQ_customer_email UNIQUE (email)
) ENGINE = INNODB;

CREATE TABLE delivery_option (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(60)   NOT NULL,
    price        DECIMAL(8,2)  NOT NULL DEFAULT 0,
    description  VARCHAR(200)  NULL,
    CONSTRAINT UQ_delivery_name UNIQUE (name),
    CONSTRAINT CHK_delivery_price CHECK (price >= 0)
) ENGINE = INNODB;

CREATE TABLE payment_method (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(50) NOT NULL,
    CONSTRAINT UQ_payment_method_name UNIQUE (name)
) ENGINE = INNODB;

CREATE TABLE orders (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    customer_id         INT          NOT NULL,
    delivery_option_id  INT          NOT NULL,
    order_datetime      DATETIME     NOT NULL,
    status              ENUM('new','paid','delivered','cancelled') NOT NULL DEFAULT 'new',
    delivery_address    VARCHAR(200) NULL,
    CONSTRAINT FK_orders_customer FOREIGN KEY (customer_id)        REFERENCES customer (id),
    CONSTRAINT FK_orders_delivery FOREIGN KEY (delivery_option_id) REFERENCES delivery_option (id)
) ENGINE = INNODB;

-- квиток на подію (одне місце на подію = один квиток)
CREATE TABLE ticket (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT         NOT NULL,
    event_seat_id  INT         NOT NULL,
    ticket_code    VARCHAR(20) NOT NULL,
    CONSTRAINT UQ_ticket_event_seat UNIQUE (event_seat_id),
    CONSTRAINT UQ_ticket_code       UNIQUE (ticket_code),
    CONSTRAINT FK_ticket_order      FOREIGN KEY (order_id)      REFERENCES orders (id),
    CONSTRAINT FK_ticket_event_seat FOREIGN KEY (event_seat_id) REFERENCES event_seat (id)
) ENGINE = INNODB;

CREATE TABLE transport_route (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    transport_type      ENUM('train','plane','bus') NOT NULL,
    carrier             VARCHAR(60)   NOT NULL,
    route_number        VARCHAR(20)   NOT NULL,
    from_city_id        INT           NOT NULL,
    to_city_id          INT           NOT NULL,
    departure_datetime  DATETIME      NOT NULL,
    arrival_datetime    DATETIME      NOT NULL,
    base_price          DECIMAL(10,2) NOT NULL,
    CONSTRAINT CHK_route_price CHECK (base_price >= 0),
    CONSTRAINT CHK_route_time  CHECK (arrival_datetime > departure_datetime),
    CONSTRAINT FK_route_from FOREIGN KEY (from_city_id) REFERENCES city (id),
    CONSTRAINT FK_route_to   FOREIGN KEY (to_city_id)   REFERENCES city (id)
) ENGINE = INNODB;

CREATE TABLE transport_ticket (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    order_id         INT           NOT NULL,
    route_id         INT           NOT NULL,
    passenger_name   VARCHAR(100)  NOT NULL,
    seat_label       VARCHAR(10)   NOT NULL,
    price            DECIMAL(10,2) NOT NULL,
    CONSTRAINT UQ_transport_seat UNIQUE (route_id, seat_label),
    CONSTRAINT CHK_transport_ticket_price CHECK (price >= 0),
    CONSTRAINT FK_transport_ticket_order FOREIGN KEY (order_id) REFERENCES orders (id),
    CONSTRAINT FK_transport_ticket_route FOREIGN KEY (route_id) REFERENCES transport_route (id)
) ENGINE = INNODB;

CREATE TABLE payment (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    order_id           INT           NOT NULL,
    payment_method_id  INT           NOT NULL,
    amount             DECIMAL(10,2) NOT NULL,
    paid_at            DATETIME      NULL,
    status             ENUM('success','pending','failed','refunded') NOT NULL DEFAULT 'pending',
    CONSTRAINT CHK_payment_amount CHECK (amount >= 0),
    CONSTRAINT FK_payment_order  FOREIGN KEY (order_id)          REFERENCES orders (id),
    CONSTRAINT FK_payment_method FOREIGN KEY (payment_method_id) REFERENCES payment_method (id)
) ENGINE = INNODB;

-- ---------------------------------------------------------------------
-- ДОДАТКОВІ ІНДЕКСИ (за результатами аналізу типових запитів)
-- ---------------------------------------------------------------------
-- пошук подій за датою
CREATE INDEX idx_event_start_datetime ON event (start_datetime);
-- пошук вільних місць на подію
CREATE INDEX idx_event_seat_event_status ON event_seat (event_id, status);
-- пошук клієнта за прізвищем та ім'ям
CREATE INDEX idx_customer_name ON customer (last_name, first_name);
-- пошук рейсів: звідки, куди, коли
CREATE INDEX idx_route_search ON transport_route (from_city_id, to_city_id, departure_datetime);
-- історія замовлень за датою
CREATE INDEX idx_orders_datetime ON orders (order_datetime);

-- ---------------------------------------------------------------------
-- INSERT (порядок: спочатку довідники, потім залежні таблиці)
-- ---------------------------------------------------------------------
INSERT INTO country (id, name, iso_code) VALUES
 (1, 'Ukraine', 'UA'),
 (2, 'Poland', 'PL'),
 (3, 'Germany', 'DE'),
 (4, 'Czech Republic', 'CZ'),
 (5, 'Slovakia', 'SK'),
 (6, 'Romania', 'RO'),
 (7, 'Hungary', 'HU'),
 (8, 'Lithuania', 'LT'),
 (9, 'United Kingdom', 'GB'),
 (10, 'United States', 'US');

INSERT INTO city (id, country_id, name) VALUES
 (1, 1, 'Lviv'),
 (2, 1, 'Kyiv'),
 (3, 1, 'Odesa'),
 (4, 1, 'Kharkiv'),
 (5, 1, 'Dnipro'),
 (6, 2, 'Warsaw'),
 (7, 2, 'Krakow'),
 (8, 3, 'Berlin'),
 (9, 4, 'Prague'),
 (10, 5, 'Bratislava'),
 (11, 1, 'Uzhhorod'),
 (12, 1, 'Ivano-Frankivsk');

INSERT INTO venue (id, city_id, name, address, capacity) VALUES
 (1, 1, 'Arena Lviv', 'Stryiska St, 199', 34915),
 (2, 1, 'Lviv National Opera', 'Svobody Ave, 28', 1100),
 (3, 2, 'Palace of Sports', 'Sportyvna Sq, 1', 10000),
 (4, 2, 'NSC Olimpiyskiy', 'Velyka Vasylkivska St, 55', 70050),
 (5, 3, 'Odesa Opera House', 'Tchaikovskoho Ln, 1', 1600),
 (6, 4, 'Kharkiv Philharmonic', 'Rymarska St, 21', 900),
 (7, 5, 'Dnipro Arena', 'Marshala Zhukova St, 1', 31003),
 (8, 1, 'Lviv Palace of Arts', 'Kopernyka St, 17', 1500),
 (9, 2, 'Stereo Plaza', 'Gnata Khotkevycha St, 1', 2500),
 (10, 12, 'Ivano-Frankivsk Drama Theatre', 'Nezalezhnosti St, 4', 800);

INSERT INTO event_type (id, name) VALUES
 (1, 'Concert'),
 (2, 'Theatre'),
 (3, 'Opera'),
 (4, 'Ballet'),
 (5, 'Festival'),
 (6, 'Stand-up'),
 (7, 'Sports match'),
 (8, 'Exhibition'),
 (9, 'Musical'),
 (10, 'Circus');

INSERT INTO artist (id, country_id, name, genre, bio) VALUES
 (1, 1, 'Okean Elzy', 'Rock', 'Ukrainian rock band founded in Lviv in 1994.'),
 (2, 1, 'Kalush Orchestra', 'Hip-hop / Folk', 'Ukrainian folk-rap group, Eurovision 2022 winners.'),
 (3, 1, 'Jamala', 'Pop / Jazz', 'Ukrainian singer, Eurovision 2016 winner.'),
 (4, 1, 'The Hardkiss', 'Alternative rock', 'Kyiv-based band fronted by Julia Sanina.'),
 (5, 1, 'Antytila', 'Pop rock', 'Ukrainian pop-rock band formed in 2008.'),
 (6, 1, 'Skofka', 'Ska / Rock', 'Ukrainian ska band from Lviv.'),
 (7, 1, 'Pianoboy', 'Pop', 'Ukrainian singer-songwriter and pianist.'),
 (8, 3, 'Scorpions', 'Hard rock', 'German hard rock band founded in 1965.'),
 (9, 10, 'Imagine Dragons', 'Pop rock', 'American band from Las Vegas.'),
 (10, 1, 'Lviv Opera Orchestra', 'Classical', 'Orchestra of the Lviv National Opera.');

INSERT INTO event (id, event_type_id, venue_id, title, description, start_datetime, status) VALUES
 (1, 1, 1, 'Okean Elzy Anniversary Tour', 'Big anniversary concert in Lviv.', '2026-12-05 19:00:00', 'scheduled'),
 (2, 1, 8, 'Kalush Orchestra Live', 'Live show with new album.', '2026-11-20 19:30:00', 'scheduled'),
 (3, 1, 3, 'Jamala Evening', 'Pop and jazz night.', '2026-12-12 19:00:00', 'scheduled'),
 (4, 1, 8, 'The Hardkiss Acoustic', 'Acoustic set in a chamber atmosphere.', '2026-11-28 20:00:00', 'scheduled'),
 (5, 1, 7, 'Antytila Charity Concert', 'Charity concert for the Armed Forces.', '2026-12-18 18:00:00', 'scheduled'),
 (6, 4, 2, 'Swan Lake', 'Classical ballet by Tchaikovsky.', '2026-11-15 18:00:00', 'scheduled'),
 (7, 1, 4, 'Scorpions Rock Believer', 'World tour stop in Kyiv.', '2027-06-10 20:00:00', 'scheduled'),
 (8, 1, 4, 'Imagine Dragons Live', 'Open-air stadium concert.', '2027-07-02 20:00:00', 'scheduled'),
 (9, 6, 8, 'Stand-up Night Lviv', 'Evening of stand-up comedy.', '2026-11-25 19:00:00', 'scheduled'),
 (10, 3, 2, 'Carmen', 'Opera by Georges Bizet.', '2026-12-20 18:00:00', 'scheduled');

INSERT INTO event_artist (event_id, artist_id) VALUES
 (1, 1), (1, 2),
 (2, 2),
 (3, 3), (3, 6),
 (4, 4),
 (5, 5),
 (6, 10),
 (7, 8),
 (8, 9),
 (9, 7),
 (10, 10);

INSERT INTO seat (id, venue_id, sector, row_no, seat_no) VALUES
 (1, 1, 'A', 1, 1),
 (2, 1, 'A', 1, 2),
 (3, 1, 'A', 1, 3),
 (4, 1, 'A', 1, 4),
 (5, 1, 'VIP', 1, 1),
 (6, 1, 'VIP', 1, 2),
 (7, 2, 'Parterre', 3, 5),
 (8, 2, 'Parterre', 3, 6),
 (9, 2, 'Parterre', 3, 7),
 (10, 8, 'Balcony', 2, 1),
 (11, 8, 'Balcony', 2, 2),
 (12, 8, 'Balcony', 2, 3);

INSERT INTO event_seat (id, event_id, seat_id, price, status) VALUES
 (1, 1, 1, 1500.00, 'sold'),
 (2, 1, 2, 1500.00, 'sold'),
 (3, 1, 3, 1500.00, 'available'),
 (4, 1, 4, 1500.00, 'sold'),
 (5, 1, 5, 3500.00, 'sold'),
 (6, 1, 6, 3500.00, 'available'),
 (7, 6, 7, 800.00, 'sold'),
 (8, 6, 8, 800.00, 'sold'),
 (9, 6, 9, 800.00, 'available'),
 (10, 2, 10, 1200.00, 'sold'),
 (11, 2, 11, 1200.00, 'available'),
 (12, 9, 12, 600.00, 'sold'),
 (13, 10, 7, 900.00, 'sold'),
 (14, 4, 10, 1000.00, 'sold');

INSERT INTO customer (id, first_name, last_name, email, phone, registered_at) VALUES
 (1, 'Ivan', 'Petrenko', 'ivan.petrenko@example.com', '+380501110001', '2026-01-10 10:00:00'),
 (2, 'Olena', 'Kovalenko', 'olena.kovalenko@example.com', '+380501110002', '2026-02-14 12:30:00'),
 (3, 'Andrii', 'Shevchenko', 'andrii.shevchenko@example.com', '+380501110003', '2026-03-01 09:15:00'),
 (4, 'Maria', 'Bondarenko', 'maria.bondarenko@example.com', '+380501110004', '2026-03-22 18:45:00'),
 (5, 'Taras', 'Melnyk', 'taras.melnyk@example.com', '+380501110005', '2026-04-05 14:20:00'),
 (6, 'Sofiia', 'Tkachenko', 'sofiia.tkachenko@example.com', '+380501110006', '2026-04-18 11:00:00'),
 (7, 'Dmytro', 'Kravchenko', 'dmytro.kravchenko@example.com', '+380501110007', '2026-05-03 16:10:00'),
 (8, 'Yulia', 'Savchenko', 'yulia.savchenko@example.com', '+380501110008', '2026-06-12 08:40:00'),
 (9, 'Oleh', 'Lysenko', 'oleh.lysenko@example.com', '+380501110009', '2026-07-07 19:25:00'),
 (10, 'Natalia', 'Moroz', 'natalia.moroz@example.com', '+380501110010', '2026-08-30 13:05:00');

INSERT INTO delivery_option (id, name, price, description) VALUES
 (1, 'E-ticket by email', 0.00, 'PDF ticket sent to email'),
 (2, 'Nova Poshta branch', 70.00, 'Pick up at Nova Poshta branch'),
 (3, 'Nova Poshta locker', 60.00, 'Pick up from parcel locker'),
 (4, 'Ukrposhta', 50.00, 'Delivery by Ukrposhta'),
 (5, 'Courier', 100.00, 'Courier delivery to address'),
 (6, 'Box office pickup', 0.00, 'Pick up at the box office'),
 (7, 'Meest', 80.00, 'Delivery by Meest'),
 (8, 'QR in mobile app', 0.00, 'QR code in the mobile app'),
 (9, 'Justin', 65.00, 'Delivery by Justin'),
 (10, 'Express courier', 200.00, 'Same-day courier delivery');

INSERT INTO payment_method (id, name) VALUES
 (1, 'Visa'),
 (2, 'Mastercard'),
 (3, 'Apple Pay'),
 (4, 'Google Pay'),
 (5, 'PrivatPay'),
 (6, 'Cash on delivery'),
 (7, 'LiqPay'),
 (8, 'Bank transfer'),
 (9, 'PayPal'),
 (10, 'Monobank');

INSERT INTO orders (id, customer_id, delivery_option_id, order_datetime, status, delivery_address) VALUES
 (1, 1, 1, '2026-10-01 10:15:00', 'paid', NULL),
 (2, 2, 2, '2026-10-02 12:00:00', 'delivered', 'Lviv, Nova Poshta branch #5'),
 (3, 3, 5, '2026-10-03 15:30:00', 'paid', 'Kyiv, Khreshchatyk St, 10, apt 5'),
 (4, 4, 8, '2026-10-04 09:45:00', 'paid', NULL),
 (5, 5, 1, '2026-10-05 20:10:00', 'paid', NULL),
 (6, 6, 6, '2026-10-06 11:20:00', 'new', NULL),
 (7, 7, 3, '2026-10-07 17:05:00', 'paid', 'Odesa, locker #112'),
 (8, 8, 1, '2026-10-08 13:40:00', 'paid', NULL),
 (9, 9, 1, '2026-10-09 08:30:00', 'paid', NULL),
 (10, 10, 8, '2026-10-10 19:00:00', 'paid', NULL),
 (11, 1, 1, '2026-10-12 14:15:00', 'paid', NULL),
 (12, 3, 1, '2026-10-14 16:50:00', 'paid', NULL);

INSERT INTO ticket (id, order_id, event_seat_id, ticket_code) VALUES
 (1, 1, 1, 'TKT-000001'),
 (2, 1, 2, 'TKT-000002'),
 (3, 2, 5, 'TKT-000003'),
 (4, 3, 7, 'TKT-000004'),
 (5, 3, 8, 'TKT-000005'),
 (6, 4, 10, 'TKT-000006'),
 (7, 5, 12, 'TKT-000007'),
 (8, 6, 4, 'TKT-000008'),
 (9, 7, 13, 'TKT-000009'),
 (10, 8, 14, 'TKT-000010');

INSERT INTO transport_route (id, transport_type, carrier, route_number, from_city_id, to_city_id, departure_datetime, arrival_datetime, base_price) VALUES
 (1, 'train', 'Ukrzaliznytsia', 'IC 705', 1, 2, '2026-11-01 06:30:00', '2026-11-01 11:45:00', 450.00),
 (2, 'train', 'Ukrzaliznytsia', 'IC 706', 2, 1, '2026-11-03 17:00:00', '2026-11-03 22:15:00', 450.00),
 (3, 'train', 'Ukrzaliznytsia', 'IC 745', 1, 11, '2026-11-05 07:10:00', '2026-11-05 11:40:00', 300.00),
 (4, 'train', 'Ukrzaliznytsia', 'IC 711', 1, 12, '2026-11-06 09:00:00', '2026-11-06 11:30:00', 250.00),
 (5, 'train', 'Ukrzaliznytsia', 'IC 743', 2, 3, '2026-11-08 08:15:00', '2026-11-08 14:50:00', 600.00),
 (6, 'train', 'Ukrzaliznytsia', 'IC 715', 2, 4, '2026-11-09 07:00:00', '2026-11-09 12:30:00', 500.00),
 (7, 'plane', 'LOT Polish Airlines', 'LO 3841', 6, 8, '2026-11-10 10:20:00', '2026-11-10 11:55:00', 1800.00),
 (8, 'plane', 'Ryanair', 'FR 1412', 7, 9, '2026-11-11 14:05:00', '2026-11-11 15:20:00', 1500.00),
 (9, 'plane', 'Lufthansa', 'LH 1621', 8, 6, '2026-11-12 18:30:00', '2026-11-12 20:05:00', 1900.00),
 (10, 'bus', 'FlixBus', 'FB 8001', 1, 7, '2026-11-14 05:45:00', '2026-11-14 11:30:00', 700.00);

INSERT INTO transport_ticket (id, order_id, route_id, passenger_name, seat_label, price) VALUES
 (1, 9, 1, 'Oleh Lysenko', '12A', 450.00),
 (2, 9, 1, 'Iryna Lysenko', '12B', 450.00),
 (3, 9, 2, 'Oleh Lysenko', '07C', 450.00),
 (4, 10, 5, 'Natalia Moroz', '03A', 600.00),
 (5, 10, 5, 'Petro Moroz', '03B', 600.00),
 (6, 11, 7, 'Ivan Petrenko', '14A', 1800.00),
 (7, 11, 7, 'Kateryna Petrenko', '14B', 1800.00),
 (8, 11, 9, 'Ivan Petrenko', '21C', 1900.00),
 (9, 12, 10, 'Andrii Shevchenko', '05', 700.00),
 (10, 12, 10, 'Halyna Shevchenko', '06', 700.00);

INSERT INTO payment (id, order_id, payment_method_id, amount, paid_at, status) VALUES
 (1, 1, 1, 3000.00, '2026-10-01 10:17:00', 'success'),
 (2, 2, 2, 3570.00, '2026-10-02 12:03:00', 'success'),
 (3, 3, 3, 1700.00, '2026-10-03 15:33:00', 'success'),
 (4, 4, 3, 1200.00, '2026-10-04 09:47:00', 'success'),
 (5, 5, 4, 600.00, '2026-10-05 20:12:00', 'success'),
 (6, 6, 6, 1500.00, NULL, 'pending'),
 (7, 7, 7, 960.00, '2026-10-07 17:08:00', 'success'),
 (8, 8, 10, 1000.00, '2026-10-08 13:42:00', 'success'),
 (9, 9, 5, 1350.00, '2026-10-09 08:33:00', 'success'),
 (10, 10, 10, 1200.00, '2026-10-10 19:02:00', 'success'),
 (11, 11, 9, 5500.00, '2026-10-12 14:18:00', 'success'),
 (12, 12, 8, 1400.00, '2026-10-14 16:55:00', 'success');

-- ---------------------------------------------------------------------
-- ВИВІД ТАБЛИЦЬ БАЗИ ДАНИХ
-- ---------------------------------------------------------------------
SHOW TABLES;

SELECT * FROM country;
SELECT * FROM city;
SELECT * FROM venue;
SELECT * FROM event_type;
SELECT * FROM artist;
SELECT * FROM event;
SELECT * FROM event_artist;
SELECT * FROM seat;
SELECT * FROM event_seat;
SELECT * FROM customer;
SELECT * FROM delivery_option;
SELECT * FROM payment_method;
SELECT * FROM orders;
SELECT * FROM ticket;
SELECT * FROM transport_route;
SELECT * FROM transport_ticket;
SELECT * FROM payment;

-- ---------------------------------------------------------------------
-- ПЕРЕВІРОЧНІ ЗАПИТИ
-- ---------------------------------------------------------------------
-- Вільні місця на подію №1
SELECT s.sector, s.row_no, s.seat_no, es.price
  FROM event_seat es JOIN seat s ON s.id = es.seat_id
 WHERE es.event_id = 1 AND es.status = 'available';

-- Сума замовлення (квитки на події + транспорт + доставка)
SELECT o.id AS order_id,
       COALESCE((SELECT SUM(es.price) FROM ticket t JOIN event_seat es ON es.id = t.event_seat_id WHERE t.order_id = o.id),0)
     + COALESCE((SELECT SUM(price) FROM transport_ticket WHERE order_id = o.id),0)
     + d.price AS total
  FROM orders o JOIN delivery_option d ON d.id = o.delivery_option_id;
