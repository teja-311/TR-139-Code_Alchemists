import math
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.vaccine_knowledge import get_vaccine_info

def calculate_viability_loss(vaccine_name, breach_temp, duration_hours):
    """
    Calculates the percentage of viability loss utilizing a simplified Q10 formulation.
    
    Args:
        vaccine_name (str): The name of the vaccine.
        breach_temp (float): The extreme temperature reached during the breach.
        duration_hours (float): Hours the breach lasted.
        
    Returns:
        float: Percentage of viability loss (0.0 to 100.0)
    """
    info = get_vaccine_info(vaccine_name)
    if not info:
        return 0.0
        
    # If the breach temperature is within the target range, no loss.
    target_min, target_max = info['temp_range']
    if target_min <= breach_temp <= target_max:
        return 0.0
        
    if breach_temp < target_min and not info['freeze_sensitive']:
        return 0.0 # Not sensitive to freezing (e.g. OPV deep freeze is okay, but 2-8 preferred in PHC)
        
    if breach_temp > target_max and not info['heat_sensitive']:
        return 0.0 # Extremely rare, but defensive coding.
        
    # Baseline degradation rate per hour at reference temperature (e.g., 8C)
    # Assume absolute failure (100% loss) happens in 72 hours at 25C for a heat sensitive vaccine
    # This is a mathematical simulation constant.
    base_k = 0.5  # % loss per hour at reference extreme (e.g. 10 degrees above max)
    
    q10 = info['q10_factor']
    
    if breach_temp > target_max:
        delta_T = breach_temp - target_max
    else: # Cold breach
        delta_T = target_min - breach_temp
        # For cold breaches, if it's freeze sensitive, degradation is extremely fast (often instant destruction)
        if info['freeze_sensitive'] and breach_temp <= 0.0:
            # Freezing destroys aluminum adjuvanted vaccines almost immediately
            return min(100.0, duration_hours * 50.0) # 2 hours to complete destruction
            
    # Arrhenius / Q10 multiplier
    # Rate = Rate_ref * Q10 ^ (delta_T / 10)
    rate = base_k * math.pow(q10, (delta_T / 10.0))
    loss_percent = rate * duration_hours
    
    # Add a time exponent for non-linear decay
    loss_percent = loss_percent * (1 + math.log10(max(1, duration_hours)))
    
    return min(100.0, loss_percent)

def get_tier_from_loss(loss_percent):
    """Returns the string tier corresponding to the percentage loss."""
    tier_idx = int(loss_percent // 10)
    if tier_idx > 9: tier_idx = 9
    
    start = tier_idx * 10
    end = min((tier_idx + 1) * 10, 100)
    return f"{start}-{end}%"
