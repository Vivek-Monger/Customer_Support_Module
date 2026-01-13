/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, useRef, onPatched } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { markup } from "@odoo/owl";

class FAQDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            faqs: [],
            categories: [],
            showForm: false,
            editingId: null,
            question: '',
            answer: '',
            categoryId: null,
        });

        onWillStart(async () => {
            await this.loadCategories();
            await this.loadFAQs();
        });
    }

    async loadFAQs() {
        try {
            const faqs = await this.orm.searchRead(
                "customer.support.faq",
                [['active', '=', true]],
                ["id", "name", "answer", "last_updated", "category_id"],
                { order: "sequence, id" }
            );
            
            this.state.faqs = faqs.map(faq => ({
                id: faq.id,
                name: faq.name,
                answer: faq.answer || '',  // Keep raw HTML, don't use markup() here
                answerMarkup: markup(faq.answer || ''),  // Separate field for display
                last_updated: faq.last_updated ? this.formatDate(faq.last_updated) : '',
                category_id: faq.category_id ? faq.category_id[0] : null,
            }));
        } catch (error) {
            console.error("Error loading FAQs:", error);
            this.notification.add("Error loading FAQs", {
                type: 'danger',
            });
        }
    }

    async loadCategories() {
        try {
            const categories = await this.orm.searchRead(
                "customer.support.faq.category",
                [['active', '=', true]],
                ["id", "name"],
                { order: "sequence, name" }
            );
            this.state.categories = categories;
        } catch (error) {
            console.error("Error loading categories:", error);
        }
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
    }

    showAddForm() {
        this.state.showForm = true;
        this.state.editingId = null;
        this.state.question = '';
        this.state.answer = '';
        this.state.categoryId = this.state.categories.length > 0 ? this.state.categories[0].id : null;
    }

    hideForm() {
        this.state.showForm = false;
        this.state.editingId = null;
        this.state.question = '';
        this.state.answer = '';
        this.state.categoryId = null;
    }

    async saveFAQ() {
        if (!this.state.question.trim() || !this.state.answer.trim()) {
            this.notification.add('Please fill in both question and answer', {
                type: 'warning',
            });
            return;
        }

        // Check if category is required and not provided
        if (!this.state.categoryId && this.state.categories.length > 0) {
            this.notification.add('Please select a category', {
                type: 'warning',
            });
            return;
        }

        try {
            const vals = {
                name: this.state.question,
                answer: this.state.answer,
            };
            
            // Only add category_id if it's set
            if (this.state.categoryId) {
                vals.category_id = this.state.categoryId;
            }

            if (this.state.editingId) {
                // Update existing FAQ
                await this.orm.write(
                    "customer.support.faq",
                    [this.state.editingId],
                    vals
                );
                this.notification.add('FAQ updated successfully', {
                    type: 'success',
                });
            } else {
                // Create new FAQ
                await this.orm.create(
                    "customer.support.faq",
                    [vals]
                );
                this.notification.add('FAQ created successfully', {
                    type: 'success',
                });
            }
            
            await this.loadFAQs();
            this.hideForm();
        } catch (error) {
            console.error("Error saving FAQ:", error);
            this.notification.add('Error saving FAQ', {
                type: 'danger',
            });
        }
    }

    async editFAQ(faq) {
        this.state.showForm = true;
        this.state.editingId = faq.id;
        this.state.question = faq.name;
        this.state.answer = faq.answer;  // Use raw HTML, not markup version
        this.state.categoryId = faq.category_id || (this.state.categories.length > 0 ? this.state.categories[0].id : null);
    }

    async deleteFAQ(faqId) {
        if (!confirm('Are you sure you want to delete this FAQ?')) {
            return;
        }

        try {
            await this.orm.unlink("customer.support.faq", [faqId]);
            this.notification.add('FAQ deleted successfully', {
                type: 'success',
            });
            await this.loadFAQs();
        } catch (error) {
            console.error("Error deleting FAQ:", error);
            this.notification.add('Error deleting FAQ', {
                type: 'danger',
            });
        }
    }

    onQuestionChange(ev) {
        this.state.question = ev.target.value;
    }

    onAnswerChange(ev) {
        this.state.answer = ev.target.value;
    }

    onCategoryChange(ev) {
        this.state.categoryId = parseInt(ev.target.value);
    }
}

FAQDashboard.template = "customer_support_module.FAQDashboardTemplate";

registry.category("actions").add("faq_dashboard", FAQDashboard);