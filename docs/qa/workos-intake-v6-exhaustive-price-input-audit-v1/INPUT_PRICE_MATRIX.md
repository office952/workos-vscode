# INPUT_PRICE_MATRIX

Generated: 2026-08-10T11:57:23.335909+00:00

| scenario | lane | baseline | field | value | EXPECTED | OBSERVED | DEFECT | severity | FIRST_BROKEN | LINE | COMPLETE_OFFER | TOTAL_DELTA |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_FACE_none | gradi | GRADI_EUR_SAFE | `finish_setup.face_finish_type` | `none` | NO | PRICED_LINE | False | - | NONE | priced_delta | total_valid | -20.8527 |
| A_FACE_oracal_641 | gradi | GRADI_EUR_SAFE | `finish_setup.face_finish_type` | `oracal_641` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | -8.8466 |
| A_FACE_oracal_651 | gradi | GRADI_EUR_SAFE | `finish_setup.face_finish_type` | `oracal_651` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | -10.7423 |
| A_FACE_oracal_8500 | gradi | GRADI_EUR_SAFE | `finish_setup.face_finish_type` | `oracal_8500` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_FACE_print_laminate | gradi | GRADI_EUR_SAFE | `finish_setup.face_finish_type` | `print_laminate` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | -4.4233 |
| A_FACE_8500_W1000 | gradi | GRADI_EUR_SAFE | `finish_setup.face_vinyl_roll_width_mm` | `1000` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 4.4233 |
| A_FACE_COLOR_032 | gradi | GRADI_EUR_SAFE | `finish_setup.face_oracal_code` | `032` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_RETURN_white_aluminum | gradi | GRADI_EUR_SAFE | `finish_setup.return_finish_type` | `white_aluminum` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_RETURN_black_aluminum | gradi | GRADI_EUR_SAFE | `finish_setup.return_finish_type` | `black_aluminum` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_RETURN_gold_aluminum | gradi | GRADI_EUR_SAFE | `finish_setup.return_finish_type` | `gold_aluminum` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_RETURN_mirror_silver | gradi | GRADI_EUR_SAFE | `finish_setup.return_finish_type` | `mirror_silver` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_RETURN_ral_paint | gradi | GRADI_EUR_SAFE | `finish_setup.return_finish_type` | `ral_paint` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 74.0863 |
| A_RETURN_oracal_wrapped | gradi | GRADI_EUR_SAFE | `finish_setup.return_finish_type` | `oracal_wrapped` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 10.1603 |
| A_DEPTH_30 | gradi | GRADI_EUR_SAFE | `finish_setup.return_depth_mm` | `30` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_DEPTH_80 | gradi | GRADI_EUR_SAFE | `finish_setup.return_depth_mm` | `80` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_DEPTH_100 | gradi | GRADI_EUR_SAFE | `finish_setup.return_depth_mm` | `100` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_BACK_forex_10_no_bevel | gradi | GRADI_EUR_SAFE | `finish_setup.backing_mode` | `forex_10_no_bevel` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_BACK_forex_10_with_bevel | gradi | GRADI_EUR_SAFE | `finish_setup.backing_mode` | `forex_10_with_bevel` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_LED_OFF | gradi | GRADI_EUR_SAFE | `finish_setup.illuminated` | `False` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | -252.5 |
| A_LED_STRIP | gradi | GRADI_EUR_SAFE | `finish_setup.lighting_system_type` | `led_strip` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_LIGHT_COLOR_warm | gradi | GRADI_EUR_SAFE | `finish_setup.light_color` | `warm` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_LIGHT_COLOR_cool | gradi | GRADI_EUR_SAFE | `finish_setup.light_color` | `cool` | NO | ZERO_DELTA_INTENTIONAL | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_LED_POWER_1.0 | gradi | GRADI_EUR_SAFE | `finish_setup.led_module_power_w` | `1.0` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_LED_POWER_1.44 | gradi | GRADI_EUR_SAFE | `finish_setup.led_module_power_w` | `1.44` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_PSU_100 | gradi | GRADI_EUR_SAFE | `finish_setup.selected_psu_watts` | `100` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_PSU_160 | gradi | GRADI_EUR_SAFE | `finish_setup.selected_psu_watts` | `160` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_PSU_200 | gradi | GRADI_EUR_SAFE | `finish_setup.selected_psu_watts` | `200` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_MOUNT_TMPL_FOREX_ON | gradi | GRADI_EUR_SAFE | `finish_setup.mounting_template_enabled` | `True` | YES | BLOCKER | True | P1 | CPP_RULE_SELECTION | no_line_delta | blocked_or_null | 0.0 |
| A_MOUNT_TMPL_PAPER | gradi | GRADI_EUR_SAFE | `finish_setup.mounting_template_material_type` | `paper` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 7.5 |
| A_MOUNT_SITE_ON | gradi | GRADI_EUR_SAFE | `finish_setup.site_installation_included` | `True` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_MARKUP_10 | gradi | GRADI_EUR_SAFE | `commercial_inputs.markup_percent` | `10` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_DISCOUNT_5 | gradi | GRADI_EUR_SAFE | `commercial_inputs.discount_percent` | `5` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| A_MANUAL_RON_100 | gradi | GRADI_EUR_SAFE | `commercial_inputs.manual_adjustment_ron` | `100` | UNKNOWN | NO_EFFECT | False | - | NONE | no_line_delta | total_valid | 0.0 |
| A_CONFIRMED_FALSE | gradi | GRADI_EUR_SAFE | `finish_setup.confirmed / letter_group confirmed` | `False` | UNKNOWN | PRICED_LINE | True | P0 | TOTAL_COMPOSITION | priced_delta | blocked_or_null | -17.0613 |
| B_FACE_none | bond | BOND_LETTERS_ACM_OPTIONAL | `finish_setup.face_finish_type` | `none` | NO | PRICED_LINE | False | - | NONE | priced_delta | total_valid | -6.4 |
| B_FACE_oracal_641 | bond | BOND_LETTERS_ACM_OPTIONAL | `finish_setup.face_finish_type` | `oracal_641` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 1.2 |
| B_FACE_oracal_8500 | bond | BOND_LETTERS_ACM_OPTIONAL | `finish_setup.face_finish_type` | `oracal_8500` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 6.8 |
| B_FACE_print_laminate | bond | BOND_LETTERS_ACM_OPTIONAL | `finish_setup.face_finish_type` | `print_laminate` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 4.0 |
| B_RETURN_RAL | bond | BOND_LETTERS_ACM_OPTIONAL | `finish_setup.return_finish_type` | `ral_paint` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 30.0 |
| B_ACM_INCLUDE_SOLD | bond | BOND_LETTERS_ACM_OPTIONAL | `acm sold composition` | `included` | YES | PRICED_LINE | False | - | NONE | priced_delta | total_valid | 358.5 |
| B_ACM_FOLD_1 | bond | BOND_ACM_INCLUDED | `acm_panel_instance.configuration.fold_count` | `1` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| B_ACM_THICKNESS_4 | bond | BOND_ACM_INCLUDED | `acm_panel_instance.configuration.acm_thickness_mm` | `4` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| B_ACM_L1_80 | bond | BOND_ACM_INCLUDED | `acm_panel_instance.configuration.l1_mm` | `80` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| B_ACM_FOIL_AFTER_FRAME | bond | BOND_ACM_INCLUDED | `shell_finish.apply_after_frame` | `True` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| B_ACM_SHEET_COLORAT | bond | BOND_ACM_INCLUDED | `sheet_material.variant` | `colorat` | YES | NO_EFFECT | True | P1 | CPP_RULE_SELECTION | no_line_delta | total_valid | 0.0 |
| B_MANUAL_RON_100 | bond | BOND_ACM_INCLUDED | `commercial_inputs.manual_adjustment_ron` | `100` | UNKNOWN | NO_EFFECT | False | - | NONE | no_line_delta | total_valid | 0.0 |
