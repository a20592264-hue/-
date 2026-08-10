import flet as ft
import requests
import json
import os
import time
from datetime import datetime

DATA_FILE = "routine_data.json"

def main(page: ft.Page):
    page.title = "Pro 루틴 매니저 (마스터 버전)"
    page.window_width = 420
    page.window_height = 850
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.DARK

    # 🔥 에러 나던 아이콘 대신 100% 안전한 텍스트 버튼으로 교체
    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        theme_btn.text = "🌞 라이트 모드" if page.theme_mode == ft.ThemeMode.LIGHT else "🌙 다크 모드"
        page.update()

    theme_btn = ft.ElevatedButton("🌙 다크 모드", on_click=toggle_theme)
    page.appbar = ft.AppBar(
        title=ft.Text("Pro 루틴 매니저", weight="bold"),
        center_title=True,
        actions=[theme_btn]
    )

    days = ["월", "화", "수", "목", "금", "토", "일"]

    def load_data():
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: pass
        return {}

    app_data = load_data()
    today_str = datetime.now().strftime("%Y-%m-%d")
    saved_date = app_data.get("last_date", "")

    raw_study = app_data.get("study_tasks", {})
    if isinstance(raw_study, list): study_tasks = {d: ([] if d != "월" else raw_study) for d in days}
    else:
        study_tasks = raw_study
        for d in days:
            if d not in study_tasks: study_tasks[d] = []

    workout_routines = app_data.get("workout_routines", {day: [] for day in days})
    for d in days:
        if d not in workout_routines: workout_routines[d] = []
        for task in workout_routines[d]:
            if "sets" not in task: task["sets"] = []

    inbody_records = app_data.get("inbody_records", [])
    
    dday_name = app_data.get("dday_name", "")
    dday_date = app_data.get("dday_date", "")

    if saved_date != today_str:
        diet_records = []
        water_records = []
        for day_tasks in study_tasks.values():
            for task in day_tasks:
                task.update({"completed": False, "time": 0, "is_running": False, "start_time": 0})
        for day_routines in workout_routines.values():
            for w in day_routines:
                w["completed"] = False
                if "sets" in w:
                    for s in w["sets"]: s["completed"] = False
    else:
        diet_records = app_data.get("diet_records", [])
        water_records = app_data.get("water_records", [])

    def save_all_data():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "last_date": today_str,
                "diet_records": diet_records,
                "water_records": water_records,
                "study_tasks": study_tasks,
                "workout_routines": workout_routines,
                "inbody_records": inbody_records,
                "dday_name": dday_name,
                "dday_date": dday_date
            }, f, ensure_ascii=False, indent=4)

    # ==========================================
    # 🎯 D-Day (목표일) 위젯
    # ==========================================
    dday_display = ft.Text("목표 설정이 필요합니다 🎯", size=16, weight="bold", color="orange")
    
    def update_dday():
        if dday_name and dday_date:
            try:
                target = datetime.strptime(dday_date, "%Y-%m-%d")
                today = datetime.strptime(today_str, "%Y-%m-%d")
                diff = (target - today).days
                if diff > 0: dday_display.value = f"🔥 {dday_name}까지 D-{diff}일 남았습니다!"
                elif diff == 0: dday_display.value = f"🎉 오늘은 {dday_name} 당일입니다!"
                else: dday_display.value = f"🏁 {dday_name} 완료 (D+{-diff})"
            except:
                dday_display.value = "⚠️ D-Day 날짜 형식이 잘못되었습니다 (YYYY-MM-DD)"
        else:
            dday_display.value = "🎯 클릭하여 목표 D-Day를 설정하세요"

    dday_input_name = ft.TextField(label="목표 (예: 모의고사, 바디프로필)")
    dday_input_date = ft.TextField(label="날짜 (예: 2026-11-15)")

    def save_dday_action(e):
        nonlocal dday_name, dday_date
        dday_name = dday_input_name.value.strip()
        dday_date = dday_input_date.value.strip()
        save_all_data()
        update_dday()
        if hasattr(page, "close"): page.close(dday_dlg)
        else: dday_dlg.open = False
        page.update()

    dday_dlg = ft.AlertDialog(
        title=ft.Text("목표 D-Day 설정"),
        content=ft.Column([dday_input_name, dday_input_date], height=130),
        actions=[ft.TextButton("저장", on_click=save_dday_action)]
    )

    def open_dday_dlg(e):
        dday_input_name.value = dday_name
        dday_input_date.value = dday_date
        if hasattr(page, "open"): page.open(dday_dlg)
        else:
            page.dialog = dday_dlg
            dday_dlg.open = True
            page.update()

    dday_container = ft.Container(
        content=dday_display, padding=10, bgcolor="#2a2a2a",
        border_radius=10, on_click=open_dday_dlg, ink=True
    )
    update_dday()

    action_to_execute = []
    def handle_confirm(e):
        confirm_dlg.open = False
        page.update()
        if action_to_execute:
            action_to_execute[0]()
            action_to_execute.clear()

    def handle_cancel(e):
        confirm_dlg.open = False
        page.update()
        action_to_execute.clear()

    confirm_dlg = ft.AlertDialog(
        title=ft.Text("정말 삭제할까요?", weight="bold"),
        content=ft.Text("한 번 지우면 복구할 수 없습니다.", size=14),
        actions=[
            ft.TextButton("취소", on_click=handle_cancel),
            ft.TextButton("삭제", on_click=handle_confirm, style=ft.ButtonStyle(color="red")),
        ], actions_alignment=ft.MainAxisAlignment.END,
    )
    if hasattr(page, "overlay"): page.overlay.append(confirm_dlg)
    else: page.dialog = confirm_dlg

    def confirm_delete(action):
        action_to_execute.clear()
        action_to_execute.append(action)
        confirm_dlg.open = True
        page.update()

    def get_nutrition_from_usda_api(food_name):
        query = food_name.strip().lower()
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&pageSize=1&api_key=DEMO_KEY"
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('foods'):
                nutrients = data['foods'][0].get('foodNutrients', [])
                c, p = 0.0, 0.0
                for n in nutrients:
                    if n.get('nutrientName') == 'Energy' and n.get('unitName') == 'KCAL': c = float(n.get('value', 0))
                    elif n.get('nutrientName') == 'Protein': p = float(n.get('value', 0))
                return c, p
        except: pass
        return None, None

    # 식단 및 수분 섹션
    meal_dropdown = ft.Dropdown(options=[ft.dropdown.Option("아침"), ft.dropdown.Option("점심"), ft.dropdown.Option("저녁")], value="아침", width=90)
    food_input = ft.TextField(label="영어 검색 (예: apple)", expand=2)
    gram_input = ft.TextField(label="양(g)", width=80, value="100")
    custom_food_input = ft.TextField(label="한글 음식명 직접입력", expand=2)
    custom_cal_input = ft.TextField(label="kcal", width=80)
    custom_pro_input = ft.TextField(label="단백질", width=80)
    water_input = ft.TextField(label="마신 물 (ml)", value="200", expand=True)
    
    diet_list, water_list = ft.Column(), ft.Column()
    total_cal_text = ft.Text("오늘 총 0.0 kcal 섭취", size=16, weight="bold", color="blue")
    total_pro_text = ft.Text("오늘 총 0.0 g 단백질 섭취", size=16, weight="bold", color="green")
    total_water_text = ft.Text("오늘 총 마신 물: 0 ml", size=16, weight="bold", color="cyan")

    def render_diet():
        diet_list.controls.clear()
        tc, tp = 0.0, 0.0
        for i, rec in enumerate(diet_records):
            tc += rec["cal"]; tp += rec["pro"]
            g_str = f"{rec['grams']}g" if isinstance(rec['grams'], (int, float)) else rec['grams']
            diet_list.controls.append(ft.Row([
                ft.Text(f"[{rec['meal']}] {rec['food']} ({g_str}) : {rec['cal']:.1f}kcal (단백질 {rec['pro']:.1f}g)", size=13, expand=True),
                ft.ElevatedButton("❌", color="red", data=i, on_click=lambda e: confirm_delete(lambda: (diet_records.pop(e.control.data), save_all_data(), render_diet())))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        total_cal_text.value = f"오늘 총 {tc:.1f} kcal 섭취"
        total_pro_text.value = f"오늘 총 {tp:.1f} g 단백질 섭취"
        page.update()

    def render_water():
        water_list.controls.clear()
        tw = 0.0
        for i, ml in enumerate(water_records):
            tw += ml
            water_list.controls.append(ft.Row([
                ft.Text(f"💧 +{ml} ml", size=14, expand=True),
                ft.ElevatedButton("❌", color="red", data=i, on_click=lambda e: confirm_delete(lambda: (water_records.pop(e.control.data), save_all_data(), render_water())))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        total_water_text.value = f"오늘 총 마신 물: {tw:.0f} ml"
        page.update()

    def add_food_api(e):
        fname = food_input.value.strip()
        try: g = float(gram_input.value.strip())
        except: return
        if not fname: return
        c, p = get_nutrition_from_usda_api(fname)
        if c is not None:
            diet_records.append({"meal": meal_dropdown.value, "food": fname, "grams": g, "cal": (c/100)*g, "pro": (p/100)*g})
            save_all_data(); render_diet()   
        food_input.value, gram_input.value = "", "100"
        page.update()

    def add_food_manual(e):
        fname = custom_food_input.value.strip()
        try:
            c, p = float(custom_cal_input.value.strip()), float(custom_pro_input.value.strip())
            if fname: 
                diet_records.append({"meal": meal_dropdown.value, "food": fname, "grams": "직접입력", "cal": c, "pro": p})
                save_all_data(); render_diet()
        except: pass
        custom_food_input.value, custom_cal_input.value, custom_pro_input.value = "", "", ""
        page.update()

    def add_water_amount(e):
        try: ml = float(water_input.value.strip())
        except: return
        if ml > 0:
            water_records.append(ml)
            save_all_data(); render_water()
        water_input.value = "200"
        page.update()

    diet_view = ft.Column([
        ft.Text("🍽️ 스마트 식단 및 수분", size=22, weight="bold"),
        meal_dropdown,
        ft.Row([food_input, gram_input]),
        ft.ElevatedButton("USDA API 검색 및 추가", on_click=add_food_api),
        ft.Divider(),
        ft.Row([custom_food_input, custom_cal_input, custom_pro_input]),
        ft.ElevatedButton("직접 추가", on_click=add_food_manual, bgcolor="blue", color="white"),
        ft.Divider(),
        ft.Row([water_input, ft.ElevatedButton("물 추가", on_click=add_water_amount, bgcolor="cyan", color="black")]),
        total_water_text, water_list, ft.Divider(),
        total_cal_text, total_pro_text, ft.Divider(), diet_list
    ], visible=True)

    # 공부 섹션
    study_day_dropdown = ft.Dropdown(options=[ft.dropdown.Option(d) for d in days], value="월", width=80)
    study_input = ft.TextField(label="오늘 할 공부", expand=True)
    study_list = ft.Column()
    study_progress = ft.ProgressBar(width=350, value=0.0, color="blue", bgcolor="#e0e0e0")
    total_study_time_text = ft.Text("총 공부 시간: 0분 0초", size=16, weight="bold", color="blue")

    def format_time(sec):
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return f"{h}시간 {m}분 {s}초" if h > 0 else (f"{m}분 {s}초" if m > 0 else f"{s}초")

    def render_study(e=None):
        cd = study_day_dropdown.value
        study_list.controls.clear()
        t_sec, comp_cnt = 0, 0
        tasks = study_tasks[cd]
        for i, t in enumerate(tasks):
            if t.get("completed"): comp_cnt += 1
            t_sec += t.get("time", 0)
            
            def m_cb(i): return lambda e: (study_tasks[cd][i].update({"completed": e.control.value}), save_all_data(), render_study())
            def m_tog(i):
                def t(e):
                    tk = study_tasks[cd][i]
                    if not tk.get("is_running"): tk.update({"is_running": True, "start_time": time.time()})
                    else: tk.update({"is_running": False, "time": tk.get("time",0) + (time.time() - tk.get("start_time", time.time()))})
                    save_all_data(); render_study()
                return t
            def m_del(i): return lambda e: confirm_delete(lambda: (study_tasks[cd].pop(i), save_all_data(), render_study()))

            cb = ft.Checkbox(label=t["name"], value=t["completed"], on_change=m_cb(i), expand=True)
            t_str = format_time(t["time"]) + (" (측정중...)" if t["is_running"] else "")
            study_list.controls.append(ft.Column([
                cb, ft.Row([ft.Text(t_str, size=13), ft.ElevatedButton("⏸ 정지" if t["is_running"] else "▶ 시작", color="orange" if t["is_running"] else "blue", on_click=m_tog(i)), ft.ElevatedButton("❌", color="red", on_click=m_del(i))], alignment=ft.MainAxisAlignment.END),
                ft.Divider()
            ]))
            
        study_progress.value = (comp_cnt / len(tasks)) if tasks else 0.0
        total_study_time_text.value = f"[{cd}요일] 총 공부 시간: {format_time(t_sec)}"
        page.update()

    study_day_dropdown.on_change = render_study
    def add_study(e):
        if study_input.value.strip():
            study_tasks[study_day_dropdown.value].append({"name": study_input.value.strip(), "completed": False, "time": 0, "is_running": False})
            save_all_data(); study_input.value = ""; render_study() 

    study_view = ft.Column([
        ft.Text("📚 요일별 공부 & 타이머", size=22, weight="bold"),
        study_progress, total_study_time_text,
        ft.Row([study_day_dropdown, study_input, ft.ElevatedButton("추가", on_click=add_study)]),
        ft.Divider(), study_list
    ], visible=False)

    # 운동 섹션
    workout_day_dropdown = ft.Dropdown(options=[ft.dropdown.Option(d) for d in days], value="월", width=80)
    workout_input = ft.TextField(label="운동 종목 (예: 푸쉬업)", expand=True)
    workout_list = ft.Column()
    workout_progress = ft.ProgressBar(width=350, value=0.0, color="green", bgcolor="#e0e0e0")

    def render_workout(e=None):
        cd = workout_day_dropdown.value
        workout_list.controls.clear()
        tasks = workout_routines[cd]
        comp_cnt = sum(1 for t in tasks if t.get("completed"))
        
        for i, task in enumerate(tasks):
            def m_p_cb(i): return lambda e: (workout_routines[cd][i].update({"completed": e.control.value}), [s.update({"completed": e.control.value}) for s in workout_routines[cd][i].get("sets",[])], save_all_data(), render_workout())
            def m_p_del(i): return lambda e: confirm_delete(lambda: (workout_routines[cd].pop(i), save_all_data(), render_workout()))
            
            p_cb = ft.Checkbox(label=task["name"], value=task["completed"], on_change=m_p_cb(i), expand=True)
            workout_list.controls.append(ft.Column([
                ft.Row([p_cb, ft.ElevatedButton("❌", color="red", on_click=m_p_del(i))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]))
            
            sets_col = ft.Column() 
            for j, s_item in enumerate(task.get("sets", [])):
                def m_s_cb(i, j): 
                    def oc(e):
                        workout_routines[cd][i]["sets"][j]["completed"] = e.control.value
                        sts = workout_routines[cd][i].get("sets", [])
                        if sts: workout_routines[cd][i]["completed"] = all(s["completed"] for s in sts)
                        save_all_data(); render_workout()
                    return oc
                def m_s_del(i, j): return lambda e: confirm_delete(lambda: (workout_routines[cd][i]["sets"].pop(j), save_all_data(), render_workout()))
                
                sets_col.controls.append(ft.Row([ft.Text("      ↳", color="gray"), ft.Checkbox(label=s_item["name"], value=s_item["completed"], on_change=m_s_cb(i,j), expand=True), ft.TextButton("❌", icon_color="red", on_click=m_s_del(i,j))]))

            set_inp = ft.TextField(label="예: 10kg 12회", height=40, expand=True, text_size=13)
            def m_add_s(i, inp): return lambda e: (workout_routines[cd][i]["sets"].append({"name": inp.value.strip(), "completed": False}) if inp.value.strip() else None, save_all_data(), render_workout())
            sets_col.controls.append(ft.Row([ft.Text("        ", color="transparent"), set_inp, ft.ElevatedButton("+ 세트추가", on_click=m_add_s(i, set_inp))]))
            
            workout_list.controls[-1].controls.append(sets_col)
            workout_list.controls.append(ft.Divider())
            
        workout_progress.value = (comp_cnt / len(tasks)) if tasks else 0.0
        page.update()

    workout_day_dropdown.on_change = render_workout
    def add_workout(e):
        if workout_input.value.strip():
            workout_routines[workout_day_dropdown.value].append({"name": workout_input.value.strip(), "completed": False, "sets": []})
            save_all_data(); workout_input.value = ""; render_workout() 

    inbody_weight = ft.TextField(label="체중(kg)", width=85)
    inbody_muscle = ft.TextField(label="골격근(kg)", width=95)
    inbody_fat = ft.TextField(label="체지방(%)", width=90)
    inbody_list = ft.Column()

    def render_inbody():
        inbody_list.controls.clear()
        for i, rec in reversed(list(enumerate(inbody_records))):
            inbody_list.controls.append(ft.Column([
                ft.Row([ft.Text(f"[{rec['date']}] 체중:{rec['weight']}kg / 골격근:{rec['muscle']}kg / 체지방:{rec['fat']}%", size=13, expand=True),
                        ft.ElevatedButton("❌", color="red", on_click=lambda e, i=i: confirm_delete(lambda: (inbody_records.pop(i), save_all_data(), render_inbody())))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider()
            ]))
        page.update()

    def add_inbody(e):
        try:
            inbody_records.append({"date": today_str, "weight": float(inbody_weight.value.strip()), "muscle": float(inbody_muscle.value.strip()), "fat": float(inbody_fat.value.strip())})
            save_all_data(); render_inbody()
            inbody_weight.value, inbody_muscle.value, inbody_fat.value = "", "", ""
            page.update()
        except: pass

    workout_view = ft.Column([
        ft.Text("💪 요일별 운동 루틴", size=22, weight="bold"),
        workout_progress,
        ft.Row([workout_day_dropdown, workout_input, ft.ElevatedButton("종목 추가", on_click=add_workout)]),
        ft.Divider(), workout_list,
        ft.Divider(thickness=3),
        ft.Text("📊 날짜별 인바디 변화", size=20, weight="bold"),
        ft.Row([inbody_weight, inbody_muscle, inbody_fat], alignment=ft.MainAxisAlignment.START),
        ft.ElevatedButton("오늘자 인바디 기록하기", on_click=add_inbody, bgcolor="blue", color="white"),
        ft.Divider(), inbody_list
    ], visible=False)

    def switch_tab(e):
        diet_view.visible, study_view.visible, workout_view.visible = (e.control.data == "식단"), (e.control.data == "공부"), (e.control.data == "운동")
        if study_view.visible: render_study()
        if workout_view.visible: render_workout()
        page.update()

    menu_bar = ft.Row([ft.ElevatedButton("식단", data="식단", on_click=switch_tab), ft.ElevatedButton("공부", data="공부", on_click=switch_tab), ft.ElevatedButton("운동", data="운동", on_click=switch_tab)], alignment=ft.MainAxisAlignment.CENTER)

    save_all_data()
    render_diet(); render_water(); render_study(); render_workout(); render_inbody()
    page.add(dday_container, menu_bar, ft.Divider(), diet_view, study_view, workout_view)

ft.app(target=main)
