from machine import Pin, SoftI2C, Timer, PWM, ADC # นำเข้าไลบรารีที่จำเป็นสำหรับการควบคุมอุปกรณ์
import ssd1306, framebuf, SpaceShip, Alien, Attack  # นำเข้าไลบรารีสำหรับจอ OLED, การจัดการภาพ, และสัญลักษณ์ต่าง ๆ
import time   # นำเข้าไลบรารีสำหรับการทำงานเกี่ยวกับเวลา


# การตั้งค่า I2C และจอ OLED
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))  # สร้างอินสแตนซ์ I2C โดยใช้พิน 22 และ 21
width = 128  # กำหนดความกว้างของจอ OLED
height = 64  # กำหนดความสูงของจอ OLED

buzzer = PWM(Pin(15))  # สร้างอุปกรณ์ PWM สำหรับเสียง โดยใช้พิน 15
buzzer.freq(512)  # ตั้งค่าเริ่มต้นให้ไม่มีเสียง
buzzer.duty(0)  # ตั้งค่าความดังให้เป็น 0

adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
adc_value = adc.read()

display = ssd1306.SSD1306_I2C(width, height, i2c)  # สร้างอินสแตนซ์สำหรับจอ OLED

score = 0  # กำหนดคะแนนเริ่มต้นเป็น 0

# ตั้งค่าปุ่ม
btn1 = Pin(14, Pin.IN, Pin.PULL_UP)  # ปุ่มสำหรับเลื่อนไปทางซ้าย
btn2 = Pin(12, Pin.IN, Pin.PULL_UP)  # ปุ่มสำหรับเลื่อนไปทางขวา
btn3 = Pin(27, Pin.IN, Pin.PULL_UP)  # ปุ่มสำหรับยิงกระสุน

# ขนาดและตำแหน่งเริ่มต้นของภาพยาน
W = 55  # ตำแหน่งเริ่มต้นของยานในแนวนอน
H = 45  # ตำแหน่งเริ่มต้นของยานในแนวตั้ง

interface = 0  # สถานะของ interface (0 = หน้าจอเริ่มต้น, 1 = เกม)
state = 0  # สถานะเกม (0 = ไม่เริ่มเกม, 1 = เริ่มเกม)
ChangeInterface = Timer(0)  # ตั้งค่า Timer สำหรับเปลี่ยน interface
Callbullet = Timer(1)
Bullet_active = 1  # สถานะกระสุน (1 = กระสุนพร้อมยิง)

# ตำแหน่งของกระสุน
pos_bullet_x = 0  # ตำแหน่งเริ่มต้นของกระสุนในแนวนอน
pos_bullet_y = 0  # ตำแหน่งเริ่มต้นของกระสุนในแนวตั้ง

# โหลดภาพ
bufer_Ship = SpaceShip.Ship  # โหลดภาพยาน
bufer_Alien = Alien.Action1  # โหลดภาพเอเลี่ยน
bufer_Bullet = Attack.Bullet  # โหลดภาพกระสุน

# ใช้ FrameBuffer เพื่อจัดการภาพ
Space = framebuf.FrameBuffer(bufer_Ship, 20, 23, framebuf.MONO_HLSB)  # สร้าง FrameBuffer สำหรับยาน
AlienSprite = framebuf.FrameBuffer(bufer_Alien, 10, 6, framebuf.MONO_HLSB)  # สร้าง FrameBuffer สำหรับเอเลี่ยน
AttackSprite = framebuf.FrameBuffer(bufer_Bullet, 10, 6, framebuf.MONO_HLSB)  # สร้าง FrameBuffer สำหรับกระสุน

# กำหนดขนาดและตำแหน่งของเอเลี่ยน
alien_rows = 2  # จำนวนแถวของเอเลี่ยน
alien_columns = 2  # จำนวนคอลัมน์ของเอเลี่ยน
alien_start_x = 10  # ตำแหน่งเริ่มต้นในแนวนอนของเอเลี่ยน
alien_start_y = 10  # ตำแหน่งเริ่มต้นในแนวตั้งของเอเลี่ยน
alien_spacing_x = 20  # ระยะห่างระหว่างเอเลี่ยนในแนวนอน
alien_spacing_y = 15  # ระยะห่างระหว่างเอเลี่ยนในแนวตั้ง

# สถานะเอเลี่ยน (True = ยังอยู่, False = ถูกยิง)
aliens = [[True for _ in range(alien_columns)] for _ in range(alien_rows)]  # สร้างตารางสถานะเอเลี่ยน
alien_positions = [[(alien_start_x + c * alien_spacing_x, alien_start_y + r * alien_spacing_y)
                    for c in range(alien_columns)] for r in range(alien_rows)]  # กำหนดตำแหน่งของเอเลี่ยน

# ทิศทางการเคลื่อนที่ของเอเลี่ยน (1 = ขวา, -1 = ซ้าย)
alien_direction = 1  # ทิศทางเริ่มต้นของการเคลื่อนที่ของเอเลี่ยน

bullet_timer = Timer(2)  # Timer สำหรับการเคลื่อนที่ของลูกกระสุน


notes = {
    'c': 261,
    'd': 294,
    'e': 329,
    'f': 349,
    'g': 391,
    'gS': 415,
    'a': 440,
    'aS': 455,
    'b': 466,
    'cH': 523,
    'cSH': 554,
    'dH': 587,
    'dSH': 622,
    'eH': 659,
    'fH': 698,
    'fSH': 740,
    'gH': 784,
    'gSH': 830,
    'aH': 880
}

song_playing = False
i = 0  # กำหนดให้ i เป็นตัวแปร global ที่สามารถเข้าถึงได้จากทุกฟังก์ชัน

def beep(note, duration):
    buzzer.freq(note)  # Set the frequency of the buzzer
    buzzer.duty_u16(32768)  # Set the duty cycle (half brightness)
    time.sleep(duration / 1000)  # Duration is in milliseconds
    buzzer.duty_u16(0)  # Turn off the buzzer
    time.sleep(0.05)  # Short delay between notes

def first_section():
    beep(notes['a'], 500)
    beep(notes['a'], 500)
    beep(notes['a'], 500)
    beep(notes['f'], 350)
    beep(notes['cH'], 150)
    beep(notes['a'], 500)
    beep(notes['f'], 350)
    beep(notes['cH'], 150)
    beep(notes['a'], 650)

    time.sleep(0.5)

    beep(notes['eH'], 500)
    beep(notes['eH'], 500)
    beep(notes['eH'], 500)
    beep(notes['fH'], 350)
    beep(notes['cH'], 150)
    beep(notes['gS'], 500)
    beep(notes['f'], 350)
    beep(notes['cH'], 150)
    beep(notes['a'], 650)

    time.sleep(0.5)

def second_section():
    beep(notes['aH'], 500)
    beep(notes['a'], 300)
    beep(notes['a'], 150)
    beep(notes['aH'], 500)
    beep(notes['gSH'], 325)
    beep(notes['gH'], 175)
    beep(notes['fSH'], 125)
    beep(notes['fH'], 125)
    beep(notes['fSH'], 250)

    time.sleep(0.325)

    beep(notes['aS'], 250)
    beep(notes['dSH'], 500)
    beep(notes['dH'], 325)
    beep(notes['cSH'], 175)
    beep(notes['cH'], 125)
    beep(notes['b'], 125)
    beep(notes['cH'], 250)
    time.sleep(0.35)

def play_melody():
    global song_playing  # ประกาศตัวแปร global
    if interface == 0:
        song_playing = True
        first_section()
        if interface != 0:  # ถ้าเปลี่ยน interface ให้หยุดเล่นทันที
            return

        second_section()
        if interface != 0:
            return

        beep(notes['f'], 250)
        beep(notes['gS'], 500)
        if interface != 0:
            return
        beep(notes['f'], 350)
        beep(notes['a'], 125)
        beep(notes['cH'], 500)
        beep(notes['a'], 375)
        beep(notes['cH'], 125)
        beep(notes['eH'], 650)

        if interface != 0:
            return

        second_section()

        beep(notes['f'], 250)
        beep(notes['gS'], 500)
        if interface != 0:
            return
        beep(notes['f'], 375)
        beep(notes['cH'], 125)
        beep(notes['a'], 500)
        beep(notes['f'], 375)
        beep(notes['cH'], 125)
        beep(notes['a'], 650)
    elif interface == 1:
        stop_melody()

        

def stop_melody():
    song_playing = False
    buzzer.duty_u16(0)  # ปิดเสียงของ buzzer
def reset_aliens():
    global aliens, alien_positions
    # กำหนดตำแหน่งเริ่มต้นของเอเลี่ยน
    aliens = [[True for _ in range(alien_columns)] for _ in range(alien_rows)]  # รีเซ็ตสถานะเอเลี่ยนเป็นยังอยู่
    alien_positions = [[(alien_start_x + c * alien_spacing_x, alien_start_y + r * alien_spacing_y)
                        for c in range(alien_columns)] for r in range(alien_rows)]  # รีเซ็ตตำแหน่ง

def move_aliens():
    global alien_positions, alien_direction  # ใช้ตัวแปร global
    move_down = False  # สถานะการเคลื่อนที่ลง

    # อ่านค่า potentiometer
    pot_value = adc.read()  # อ่านค่าจาก potentiometer
    # คำนวณความเร็ว (ปรับให้เหมาะสมตามความต้องการ)
    # แปลงค่า potentiometer (0-4095) ไปเป็นความเร็วที่เหมาะสม (1-20)
    speed = max(1, min(20, pot_value // 200))  # ปรับความเร็วที่นี่

    # เคลื่อนที่เอเลี่ยนแต่ละตัวไปทางขวาหรือซ้าย
    for r in range(alien_rows):
        for c in range(alien_columns):
            if aliens[r][c]:  # เช็คว่าเอเลี่ยนยังอยู่
                x, y = alien_positions[r][c]  # ดึงตำแหน่งของเอเลี่ยน
                alien_positions[r][c] = (x + alien_direction * 2, y)  # อัปเดตตำแหน่งของเอเลี่ยน

    # หาตำแหน่งซ้ายสุดและขวาสุดของเอเลี่ยนที่ยังมีชีวิต
    leftmost = width  # เริ่มต้นด้วยค่าที่มากที่สุด
    rightmost = 0     # เริ่มต้นด้วยค่าที่น้อยที่สุด

    for r in range(alien_rows):
        for c in range(alien_columns):
            if aliens[r][c]:
                x, y = alien_positions[r][c]
                if x < leftmost:
                    leftmost = x  # อัปเดตตำแหน่งซ้ายสุด
                if x > rightmost:
                    rightmost = x  # อัปเดตตำแหน่งขวาสุด

    # เปลี่ยนทิศทางและเลื่อนลงเมื่อเอเลี่ยนถึงขอบหน้าจอ
    if leftmost <= 0 or rightmost >= width - 10:
        alien_direction *= -1  # เปลี่ยนทิศทาง
        move_down = True  # สถานะการเคลื่อนที่ลงเป็นจริง

    if move_down:  # ถ้าต้องเคลื่อนที่ลง
        for r in range(alien_rows):
            for c in range(alien_columns):
                if aliens[r][c]:  # เช็คว่าเอเลี่ยนยังอยู่
                    alien_x, alien_y = alien_positions[r][c]  # ดึงตำแหน่งของเอเลี่ยน
                    alien_positions[r][c] = (alien_x, alien_y + 5)  # เลื่อนลง 5 พิกเซล

    time.sleep(speed / 1000.0)  # ควบคุมความเร็วการเคลื่อนที่ของเอเลี่ยน



def check_aliens_collision():
    global H  # ใช้ตัวแปร global
    for r in range(alien_rows):
        for c in range(alien_columns):
            if aliens[r][c]:  # เช็คว่าเอเลี่ยนยังอยู่
                alien_x, alien_y = alien_positions[r][c]  # ดึงตำแหน่งของเอเลี่ยน
                if alien_y + 6 >= H:  # ตรวจสอบการชน
                    return True  # ถ้าชนให้คืนค่า True
    return False  # ถ้าไม่ชนคืนค่า False

def buzz(frequency, duration):
    global buzzer  # ใช้ตัวแปร global
    buzzer.freq(frequency)  # กำหนดความถี่
    buzzer.duty(512)  # กำหนดความดัง (ค่า 512 ค่ากลาง)
    time.sleep(duration)  # เล่นเสียงเป็นระยะเวลาที่กำหนด
    buzzer.duty(0)  # หยุดเล่นเสียง

def fire_sound():
    buzz(128, 0.1)  # เล่นเสียงยิงกระสุน
    time.sleep(0.1)  # หยุดพักระหว่างเสียง
    


def aliendeath_sound():
    buzz(500, 0.2)  # เสียงความถี่ 500Hz นาน 0.2 วินาที
    time.sleep(0.1)  # พักก่อนสิ้นสุดเสียง

def bullet():
    global W, H, interface, pos_bullet_y, pos_bullet_x, Bullet_active, state  # ใช้ตัวแปร global
    if btn3.value() == 0 and state == 1:  # ถ้าปุ่มยิงถูกกดและอยู่ในสถานะเริ่มเกม
        if interface == 1 and Bullet_active == 1:  # เช็คว่าอยู่ในเกมและกระสุนพร้อมยิง
            pos_bullet_y = H + 10  # กำหนดตำแหน่งเริ่มต้นของกระสุน
            pos_bullet_x = W + 6  # กำหนดตำแหน่งเริ่มต้นของกระสุน
            Bullet_active = 0  # ตั้งค่ากระสุนไม่พร้อมยิง
            bulletMove()  # เรียกใช้ฟังก์ชัน bulletMove โดยตรง
            fire_sound()  # เล่นเสียงยิงกระสุน



def bulletMove():
    global pos_bullet_y, pos_bullet_x, Bullet_active, interface, aliens, alien_positions, score

    if interface == 1 and Bullet_active == 0:  # เช็คว่ากระสุนไม่พร้อมยิง
        display.fill_rect(pos_bullet_x, pos_bullet_y, 10, 6, 0)  # ลบกระสุนเดิม
        pos_bullet_y -= 5  # เคลื่อนที่กระสุนขึ้น 5 พิกเซล

        hit_alien = False  # สถานะการชนกับเอเลี่ยน

        for r in range(alien_rows):
            for c in range(alien_columns):
                if aliens[r][c]:  # ตรวจสอบว่าเอเลี่ยนยังไม่ถูกยิง
                    alien_x, alien_y = alien_positions[r][c]  # ดึงตำแหน่งของเอเลี่ยน
                    if alien_x <= pos_bullet_x <= alien_x + 10 and alien_y <= pos_bullet_y <= alien_y + 6:  # ตรวจสอบการชน
                        aliens[r][c] = False  # เอเลี่ยนถูกยิง
                        Bullet_active = 1  # รีเซ็ตกระสุน
                        score += 1  # เพิ่มคะแนนเมื่อยิงเอเลี่ยนถูก
                        display.fill_rect(alien_x, alien_y, 10, 6, 0)  # ลบเอเลี่ยนที่ถูกยิง
                        aliendeath_sound()  # เล่นเสียงการตายของเอเลี่ยน
                        reset_bullet()  # รีเซ็ตกระสุน
                        hit_alien = True  # ตั้งค่าสถานะการชนเป็นจริง

        if not hit_alien:  # ถ้าไม่ชนกับเอเลี่ยน
            display.text("*", pos_bullet_x, pos_bullet_y)  # แสดงกระสุน
            display.blit(Space, W, H)  # แสดงยาน
            display.show()  # อัปเดตจอแสดงผล
        
        if pos_bullet_y < 0:  # ถ้ากระสุนออกนอกจอ
            reset_bullet()  # รีเซ็ตกระสุน



def reset_bullet():
    global Bullet_active, pos_bullet_y, pos_bullet_x  # ใช้ตัวแปร global
    Bullet_active = 1  # รีเซ็ตสถานะกระสุน
    pos_bullet_x = 0  # รีเซ็ตตำแหน่งกระสุนในแนวนอน
    pos_bullet_y = 0  # รีเซ็ตตำแหน่งกระสุนในแนวตั้ง

def check_aliens_status():
    return all(not status for row in aliens for status in row)  # เช็คว่าเอเลี่ยนทั้งหมดถูกยิงแล้วหรือไม่

def MoveLeft():
    global W, H, interface  # ใช้ตัวแปร global
    if interface == 1:  # เช็คว่าอยู่ในเกม
        if btn1.value() == 0:  # ถ้าปุ่มเลื่อนไปทางซ้ายถูกกด
            display.fill(0)  # ลบภาพเดิม
            if W > 0:  # ถ้าตำแหน่งไม่อยู่ที่ขอบซ้าย
                W -= 5  # เลื่อนยานไปทางซ้าย 5 พิกเซล
            display.blit(Space, W, H)  # แสดงยานที่ตำแหน่งใหม่
            display.show()  # อัปเดตจอแสดงผล

def MoveRight():
    global W, H, interface  # ใช้ตัวแปร global
    if interface == 1:  # เช็คว่าอยู่ในเกม
        if btn2.value() == 0:  # ถ้าปุ่มเลื่อนไปทางขวาถูกกด
            display.fill(0)  # ลบภาพเดิม
            if W < (width - 20):  # ถ้าตำแหน่งไม่อยู่ที่ขอบขวา
                W += 5  # เลื่อนยานไปทางขวา 5 พิกเซล
            display.blit(Space, W, H)  # แสดงยานที่ตำแหน่งใหม่
            display.show()  # อัปเดตจอแสดงผล

def Change_interface(timer):
    global interface, state, W, H, Bullet_active  # ใช้ตัวแปร global
    if btn3.value() == 0:  # ถ้าปุ่มยิงถูกกด
        if state == 1:  # เช็คว่าอยู่ในสถานะเริ่มเกม
            if interface == 0:  # ถ้าอยู่ในหน้าจอเริ่มต้น
                W = 55  # รีเซ็ตตำแหน่งยาน
                H = 45  # รีเซ็ตตำแหน่งยาน
                interface = 1  # เปลี่ยนไปยังหน้าจอเกม
                stop_melody()  # หยุดเพลงเมื่อเปลี่ยนไป interface 1
                reset_aliens()
                state = 0  # รีเซ็ตสถานะ
            elif interface == 1:  # ถ้าอยู่ในหน้าจอเกม
                Bullet_active = 1  # รีเซ็ตสถานะกระสุน
                W = 55  # รีเซ็ตตำแหน่งยาน
                H = 45  # รีเซ็ตตำแหน่งยาน
                interface = 0  # กลับไปยังหน้าจอเริ่มต้น
                reset_aliens()
                state = 0  # รีเซ็ตสถานะ



def showPush(pin):  # เปลี่ยนไปให้รองรับพารามิเตอร์
    global W, state, interface  # ใช้ตัวแปร global
    if btn1.value() == 0:  # ถ้าปุ่มเลื่อนไปทางซ้ายถูกกด
        MoveLeft()  # เรียกฟังก์ชันเลื่อนไปทางซ้าย
    elif btn2.value() == 0:  # ถ้าปุ่มเลื่อนไปทางขวาถูกกด
        MoveRight()  # เรียกฟังก์ชันเลื่อนไปทางขวา
    elif btn3.value() == 0:  # ถ้าปุ่มยิงถูกกด
        if state == 0:  # เริ่มการยิงเมื่ออยู่ในสถานะเริ่มต้น
            state += 1  # เปลี่ยนสถานะเป็นเริ่มเกม
            ChangeInterface.init(period=1500, mode=Timer.ONE_SHOT, callback=Change_interface)  # เริ่ม Timer เปลี่ยน interface
    elif btn3.value() == 1:  # ถ้าปุ่มยิงถูกปล่อย
        state = 0  # รีเซ็ตสถานะ



# ตั้งค่า interrupt สำหรับปุ่ม
btn1.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=showPush)
btn2.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=showPush)
btn3.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=showPush)


# ลูปหลัก
while True:
    if interface == 0:  # ถ้าอยู่ในหน้าจอเริ่มต้น
        display.fill(0)  # ลบจอแสดงผล
        display.text("START GAME", 20, 30)  # แสดงข้อความเริ่มเกม
        display.show()  # อัปเดตจอแสดงผล
        play_melody()  
            
    elif interface == 1:  # ถ้าอยู่ในหน้าจอเกม
        display.fill(0)  # ลบจอแสดงผล
        MoveRight()  # เรียกฟังก์ชันเลื่อนไปทางขวา
        MoveLeft()  # เรียกฟังก์ชันเลื่อนไปทางซ้าย
        bullet()
        bulletMove()  # เรียกฟังก์ชันเคลื่อนที่ลูกกระสุน
        move_aliens()  # เรียกฟังก์ชันเคลื่อนที่เอเลี่ยน
        
        # แสดงเอเลี่ยนที่ยังไม่ถูกยิง
        for r in range(alien_rows):
            for c in range(alien_columns):
                if aliens[r][c]:  # เช็คว่าเอเลี่ยนยังอยู่
                    alien_x, alien_y = alien_positions[r][c]  # ดึงตำแหน่งของเอเลี่ยน
                    display.blit(AlienSprite, alien_x, alien_y)  # แสดงเอเลี่ยน

        display.blit(Space, W, H)  # แสดงยานที่ตำแหน่ง
        display.show()  # อัปเดตจอแสดงผล

        if check_aliens_status():  # เช็คว่าเอเลี่ยนทั้งหมดถูกยิงหรือไม่
            display.fill(0)  # ลบจอแสดงผล
            display.text("YOU WIN!", 20, 20)  # แสดงข้อความชนะ
            display.text("Score: " + str(score), 20, 40)  # แสดงคะแนน
            display.show()  # อัปเดตจอแสดงผล
            time.sleep(2)  # รอ 2 วินาที
            interface = 0  # กลับไปที่หน้าจอเริ่มต้น
            score = 0  # รีเซ็ตคะแนนเมื่อเริ่มเกมใหม่

        if check_aliens_collision():  # เช็คว่าเอเลี่ยนชนกับยานหรือไม่
            display.fill(0)  # ลบจอแสดงผล
            display.text("GAME OVER", 20, 20)  # แสดงข้อความเกมจบ
            display.text("Score: " + str(score), 20, 40)  # แสดงคะแนน
            display.show()  # อัปเดตจอแสดงผล
            time.sleep(2)  # รอ 2 วินาที
            interface = 0  # กลับไปที่หน้าจอเริ่มต้น
            score = 0  # รีเซ็ตคะแนนเมื่อเริ่มเกมใหม่
    adc_value = adc.read()
    print(str(interface))
    #print(str(btn3.value()))  # แสดงสถานะของปุ่มยิงในคอนโซล



