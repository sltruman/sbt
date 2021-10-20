#include "main_online.cpp"

int main()
{
	
	string a = "a 1 700 40\nb 2 600 70\nc 3 800 30";
	string b = "";
	OnlinePacking::PlanPlacement(a,b);
	OnlinePacking::ResetPallet();
	
	return 0;
}